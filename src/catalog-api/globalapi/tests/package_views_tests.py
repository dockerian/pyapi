import mock
import unittest

from pyramid import httpexceptions
from pyramid.testing import setUp, tearDown, DummyResource, DummyRequest

from .. views import package_views

from common.logger import getLogger
logger = getLogger(__name__)


class PackagesViewsTests(unittest.TestCase):
    def setUp(self):
        self.config = setUp()

    def tearDown(self):
        tearDown()

    @mock.patch('globalapi.package.get_package_list')
    def test_index(self, mock_getlist):
        mock_package_list = {
            'status': 200,
            'packages': [{'pkg1': 'test'}]
        }
        mock_getlist.return_value = mock_package_list
        request = DummyRequest()
        request.context = DummyResource()
        request.matchdict['product_id'] = 'dummy'
        request.params['filters'] = 'keyword'
        view = package_views.PackagesViews(request)

        response = view.index()
        self.assertEqual(type(response), dict)
        self.assertEqual(type(response['packages']), list)
        self.assertEqual(response['status'], 200)
        self.assertEqual(response, mock_package_list)

    @mock.patch('globalapi.package.get_package_list')
    def test_index_404(self, mock_getlist):
        mock_package_list = {'status': 404}
        mock_getlist.return_value = mock_package_list
        request = DummyRequest()
        request.context = DummyResource()
        request.matchdict['product_id'] = 'dummy'
        view = package_views.PackagesViews(request)

        response = view.index()
        self.assertIs(type(response), httpexceptions.HTTPNotFound)

    @mock.patch('globalapi.package.get_package_list')
    def test_index_500(self, mock_getlist):
        error_message = 'GET PACKAGE LIST EXCEPTION'
        mock_getlist.side_effect = \
            httpexceptions.HTTPInternalServerError(explanation=error_message,
                                                   detail=error_message)
        request = DummyRequest()
        request.context = DummyResource()
        request.matchdict['product_id'] = 'dummy'
        view = package_views.PackagesViews(request)

        response = view.index()
        self.assertEqual(response.status_code, 500)
        self.assertTrue(error_message in response.message)
        self.assertTrue(error_message in response.detail)
        self.assertTrue(len(response.json_body['errors']) > 0)
        self.assertIs(type(response), httpexceptions.HTTPInternalServerError)

    def test_index_no_product_id(self):
        request = DummyRequest()
        request.context = DummyResource()
        view = package_views.PackagesViews(request)

        response = view.index()
        self.assertTrue(response.json_body is not None)
        result = response.json_body
        self.assertTrue(result[u'errors'])

    def test_upload_no_product_id(self):
        request = DummyRequest()
        request.context = DummyResource()
        view = package_views.PackagesViews(request)

        response = view.upload()
        self.assertTrue(response.json_body is not None)
        result = response.json_body
        self.assertTrue(result[u'errors'])

    @mock.patch('pyramid.response.Response')
    @mock.patch('globalapi.package.save_package')
    def test_upload(self, mock_save, mock_response):
        fileupload = mock.MagicMock()
        fileupload.filename = 'filename on upload'
        mock_response = {'status': 201}
        mock_save.return_value = mock_response
        request = DummyRequest()
        request.context = DummyResource()
        request.matchdict['product_id'] = 'dummy'
        request.params = {'fileupload': fileupload}
        view = package_views.PackagesViews(request)

        response = view.upload()
        mock_save.assert_called_with(fileupload.filename, fileupload)
        self.assertTrue(mock_save.called)
        logger.debug(response)
        self.assertEqual(response.status_code, mock_response['status'])
        self.assertIs(type(response), httpexceptions.HTTPCreated)

    @mock.patch('pyramid.response.Response')
    @mock.patch('globalapi.package.save_package')
    def test_upload_500(self, mock_save, mock_response):
        fileupload = mock.MagicMock()
        fileupload.filename = 'filename on upload'
        error_message = "SAVE PACKAGE EXCEPTION"
        mock_save.side_effect = Exception(error_message)
        request = DummyRequest()
        request.context = DummyResource()
        request.matchdict['product_id'] = 'dummy'
        request.params = {'fileupload': fileupload}
        view = package_views.PackagesViews(request)

        response = view.upload()
        self.assertEqual(response.status_code, 500)
        self.assertTrue(error_message in response.message)
        self.assertTrue(error_message in response.detail)
        self.assertTrue(len(response.json_body['errors']) > 0)
        self.assertIs(type(response), httpexceptions.HTTPInternalServerError)


class PackageViewsTests(unittest.TestCase):
    def setUp(self):
        self.config = setUp()

    def tearDown(self):
        tearDown()

    @mock.patch('StringIO.StringIO')
    @mock.patch('globalapi.package.get_package')
    def test_get(self, mock_get_package, mock_stringIO):
        request = DummyRequest()
        request.context = DummyResource()
        request.matchdict['product_id'] = 'dummy'
        request.matchdict['package_id'] = 'test'
        import StringIO
        mock_get_package_result = {
            'status': 200,
            'file_contents': mock.Mock(),
            'headers': {
                'content-length': 4,
                'content-type': 'app',
            }}
        mock_get_package.return_value = mock_get_package_result
        mock_stringIO_result = mock.Mock()
        mock_stringIO.return_value = mock_stringIO_result
        mock_stringIO_result.read.return_value = 'body'
        view = package_views.PackageViews(request)

        response = view.get()
        self.assertEqual(response.content_length, 4)
        self.assertEqual(response.status_code, 200)
        self.assertIs(type(response), httpexceptions.HTTPOk)

    @mock.patch('globalapi.package.get_package')
    def test_get_404(self, mock_get_package):
        request = DummyRequest()
        request.context = DummyResource()
        request.matchdict['product_id'] = 'dummy'
        request.matchdict['package_id'] = 'test'
        mock_get_package_result = {
            'status': 404,
            }
        mock_get_package.return_value = mock_get_package_result
        view = package_views.PackageViews(request)

        response = view.get()
        self.assertIs(type(response), httpexceptions.HTTPNotFound)

    @mock.patch('globalapi.package.get_package')
    def test_get_500(self, mock_get_package):
        request = DummyRequest()
        request.context = DummyResource()
        request.matchdict['product_id'] = 'dummy'
        request.matchdict['package_id'] = 'test'
        mock_get_package_result = {
            'status': 404,
            }
        error_message = "GET PACKAGE EXCEPTION"
        mock_get_package.side_effect = Exception(error_message)
        view = package_views.PackageViews(request)

        response = view.get()
        self.assertEqual(response.status_code, 500)
        self.assertTrue(error_message in response.message)
        self.assertTrue(error_message in response.detail)
        self.assertTrue(len(response.json_body['errors']) > 0)
        self.assertIs(type(response), httpexceptions.HTTPInternalServerError)
