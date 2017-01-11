# GitHub workflow

<br />
## Introduction to the workflow

* Company has a central paid GitHub account with one or more private repositories. These hold the "gold copy" of the repository.

* The repository has two branches. The "master" branch is what in production and "development" is what deployed to the QA server (not as same as in traditional cvs/svn/git workflows). Other long-lived branches could be "staging" server, or a "hackathon".

* This "gold copy" repository (mainly master branch) is also used with
  - CI/CD tools (e.g. building, unit tests, functional tests, staging etc.)
  - any commit/deploy gate checking
  - auto-deployment tools

* Developers/users fork the repository to their own personal GitHub account. (Note: When the user left the organization, the fork will be automatically deleted with removed account/permission.)

* Developer forks the repo, and clones from the fork (by `git clone git@github.com:username/repository-name.git`), which makes "origin" point at the personal fork.

* Developer also adds an "upstream" (naming convention) that points at the company repository (by `git add upstream git@github.com:organization-name/repository-name.git`)

* Developer uses (local) `master` and `origin/master` to sync with `upstream/master` and should never commit to any `master` branch.

* Developer always works on (local) branches, pushes to `origin` (the personal fork), and pull/rebase from `master`

* Developer uses `origin` branch to submit pull request to `upstream/master`

* Advantages
  - Follow the workflow with major open source community
  - Guard core/corp components as well as encourage innovation and adoption.
  - Organize cross department/team collaboration.
  - Reduce noise (on core/corp repo branches).
  - Reduce workload for a dedicated repo admin.
  - Reduce need to maintain multiple branches.
  - Streamline interaction with contractors.
  - PR conversations on github.
  - Easier with growing team.
  - Easier for CI/CD.


<br />
## In operation

### Configure SSH and git

  1. Configure SSH to use key for github.com

    - generate authentication key for github.com

    ```
    ssh-keygen -t rsa -b 4096 -C "github.com" -f ~/.ssh/github_key
    ```

    - add the following to ~/.ssh/config

    ```
    host github.com
      HostName github.com
      PreferredAuthentications publickey,keyboard-interactive,password
      IdentityFile ~/.ssh/github_key
      IdentitiesOnly yes
      User git
    ```

    - store in mac os x key chain

    ```
    git config --global credential.helper osxkeychain
    ```

  2. Configure git

    - Default [push](https://git-scm.com/docs/git-config/#git-config-pushdefault) option

    ```
    git config --global push.default simple
    ```

    - Cache git credential

    ```
    # store credential in mac os x key chain
    git config --global credential.helper osxkeychain

    # set git to use the credential memory cache (default 15-minute)
    git config --global credential.helper cache
    # set the cache to timeout after 1 hour (setting is in seconds)
    git config --global credential.helper 'cache --timeout=3600'
    git config --global credential.https://github.com.username jzhuyx

    # store credential in keyring
    sudo apt-get install libgnome-keyring-dev
    sudo make --directory=/usr/share/doc/git/contrib/credential/gnome-keyring
    git config --global credential.helper /usr/share/doc/git/contrib/credential/gnome-keyring/git-credential-gnome-keyring
    ```

    - Diff/Merge Tool

      ```
      which opendiff
      git config --global merge.tool opendiff
      git config --global diff.tool opendiff
      git config --global difftool.prompt false
      ```
      should generate following in `~/.gitconfig`:

      ```
      [diff]
        tool = opendiff
      [merge]
        tool = opendiff
      ```

    - Graph log

      ```
      git config --global alias.lg "log --graph --pretty=format:'%Cred%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit --date=relative"
      ```
      The above is adding an alias to `~/.gitconfig`.


### Fork (one-time setup)

  1. Open and sign into github.com
  2. Open one of “dockerian” repositories (e.g. “pyapi”)
  3. On the upper-left corner (under your profile icon, e.g. “sd-white”), click on Fork
  4. On popup dialog, click on “@your-id” profile icon
  - Note: it is okay to click on Fork more than once, which won’t fork another time but shows existing forks.

### Clone and set upstream (one-time setup)

  1. Open a terminal/console
  2. Clone your forked repository:

  ```
  # Note: DO NOT use https
  # git clone https://github.com/jasonzhuyx/pyapi.git
  git clone git@github.com:jasonzhuyx/pyapi.git
  cd pyapi
  ```

  3. Add and review upstream

  ```
  # git remote remove upstream >/dev/null 2>&1
  # Note: DO NOT use https
  # git remote add upstream http://github.com/dockerian/pyapi.git
  git remote add upstream git@github.com/dockerian/pyapi.git

  git remote –v
  git fetch upstream
  ```


### Pull Request (PR)

  * <a name="sync-upstream"></a>Sync with upstream

    ```
    # git remote –v
    git fetch upstream
    git checkout master

    # reset to upstream master
    git reset --hard upstream/master

    # DON'T forget to commit to origin (your fork)
    git push -f origin master
    git status
    ```

  * Start working on a new branch (usually a new feature or fix)

    ```
    git checkout –b TIP-1234 # a task or fix associated with JIRA ticket

    # optionally with name convention, e.g.
    git checkout –b feature/TIP-1234
    git checkout –b fix/TIP-4321

    # undo any individual change
    git checkout -- changed_file_name  # undo a change
    ```

  * Commit on branch (locally)

    ```
    # doing your work and commit
    git add *
    git commit –m "fixed TIP-4321 a bug in code"

    # optionally amend your change
    # git add *
    # git commit --amend
    ```

  * Sync with upstream again (repeat this [step](#sync-upstream)) and merge with conflict

    ```
    # now sync on your origin/master
    git checkout master
    git reset --hard upstream/master
    ```

    - Merging option (1) rebase:

      ```
      git checkout TIP-1234
      git rebase master

      # fix conflict locally, and commit (again) or
      # git commit –amend

      ```

    - Merging option (2) pull:

      ```
      git checkout TIP-1234
      git pull upstream master

      # fix conflict locally, and commit (again) or
      # git commit –amend

      ```

  * Push changes to origin branch (on your fork)

    ```
    # git push --force  # origin/branch
    ```

  * Submit PR on github.com
    - open upstream repo on github.com
    - click on "Pull Request", then "New Pull Request" (green button)
    - click on "compare cross forks" link
    - provide brief description including (e.g. JIRA) ticket number
    - add comment of testing result
    - add reviewers
    - submit


## Amend historical commits

  * Listing previous logs

    ```
    git log --oneline -3  # or n, here n means last n commits
    ```
    assuming this produces

    ```
    268bb1f the last commit
    57688c5 the previous -1 commit
    e4b7303 the previous -2 commit
    ```
    and we want to edit message for `57688c5 ` - "the previous -1 commit"

  * Do an interactive rebase

    ```
    git rebase -i HEAD~3
    ```
    and this will bring up your editor with commits in reverse order:

    ```
    pick 268bb1f the last commit
    pick 57688c5 the previous -1 commit
    pick e4b7303 the previous -2 commit
    pick e4b7303 the previous -3 commit
    ```

  * Change the commend of `pick`, in the first column, to `e`

    ```
    pick e4b7303 the previous -3 commit
    pick e4b7303 the previous -2 commit
    e 57688c5 the previous -1 commit
    pick 268bb1f the last commit
    ```
    then save and quit (e.g. pressing ESC, `:wq` likely in `vi`)

  * Now amending the message by

    ```
    git commit --amend  # --author="Author Name <email@address.com>"
    ```
    this will bring up the editor to allow you editing the message, and then save and quit

  * Continue to complete

    ```
    git rebase --continue
    ```

  * Repeat last 2 steps if there are more than one commit to ammend


<br />
## Reference

### Bash aliases for git (likely in your ~/.bashrc)

```
alias a="alias|cut -d' ' -f 2- "
alias gbc='git symbolic-ref --short -q HEAD'
alias gbd='git branch -d '  # delete branch locally
alias gbdo='git push origin --delete '  # delete branch on origin
alias gbv="git branch -v "
alias gco="git checkout "
alias gfv="git fetch -v --all --prune "
alias glg="git log --graph --pretty=format:'%C(magenta)%h%Creset -%C(yellow)%d%Creset %s %Cgreen(%cr) %C(bold blue)<%an>%Creset' --abbrev-commit --date=relative"
alias gpum='git pull upstream master'
alias grm='git rebase master'
alias grmgpf='git rebase master; git push --force'
alias grv='git remote -v'
alias gst='git status'

############################################################
# function: Rename git branch name locally and on origin
############################################################
function gb-rename() {
  echo "Fetching git branches ..."
  git fetch -v --all --prune
  echo ""

  local old_name=$1
  local new_name=$2
  # get current branch, optionally using:
  #   - `git branch --no-color | grep -E '^\*' | awk '{print $2}'`
  #   - `git symbolic-ref --short -q HEAD`)
  local current_branch="$(git rev-parse --symbolic-full-name --abbrev-ref HEAD)"
  echo "Current branch: ${current_branch}"
  echo ""

  if [[ "$2" == "" ]]; then
    echo "Missing argument(s) on renaming git branch: "
    echo ""
    echo "${FUNCNAME} old_name new_name"
    echo ""
    return -2
  fi

  if [[ "$1" == "master" ]] || [[ "$2" == "master" ]]; then
    echo "Cannot rename 'master' branch."
    echo ""
    return -1
  fi

  if [[ "$1" == "${current_branch}" ]] || [[ "$2" == "${current_branch}" ]]; then
    echo "Currently on branch [${current_branch}] to be renamed: "
    echo ""
    echo "${FUNCNAME} $1 $2"
    echo ""
    return 9
  fi

  local chk_name=""
  for b in $(git branch --no-color | grep -E '^ '); do
    if [[ "${b}" == "${new_name}" ]]; then
      echo "Branch name [${new_name}] already exists."
      echo ""
      return 2
    fi
    if [[ "${b}" == "${old_name}" ]]; then
      chk_name="${old_name}"
    fi
  done

  if [[ "${chk_name}" == "" ]]; then
    echo "Cannot find branch [${old_name}]. Please fetch and sync to origin."
    echo ""
    return 1
  fi

  git branch -m ${old_name} ${new_name}
  git push origin :${old_name} ${new_name}
  git push origin -u ${new_name}

  echo ""
  echo "Done."
  echo ""
}

############################################################
# function: Delete git branch locally and on origin/remote
############################################################
function gbd-all() {
  if [[ "$1" != "" ]] && [[ "$1" != "master" ]]; then
    git push origin --delete $1
    git branch -d $1
  else
    echo "Missing valid branch name in argument."
    echo ""
  fi
  git fetch --all --prune
  git branch -v
}

```

### Git/GitHub GUI client options

  * Mac OS X
    - SourceTree (https://www.sourcetreeapp.com/)
    - GitHub Desktop (https://desktop.github.com/)
    - Addons/plugins for Atom or IDE

  * Ubuntu
    - Giggle (https://wiki.gnome.org/Apps/giggle/)
    - Gitg (`sudo apt-get install gitg`)
    - GitKraken (https://www.gitkraken.com/)
    - Git-Cola (https://git-cola.github.io)

### Diff/Merge tools

  * from GUI (e.g. SourceTree)

  * opendiff

  ```
  which opendiff
  git config --global merge.tool opendiff
  git config --global diff.tool opendiff
  git config --global difftool.prompt false
  ```

  * KDiff3 (http://kdiff3.sourceforge.net/)
    - Mac OS X: `brew install kdiff3`
    - Ubuntu: from Software Center


### Links

Quick tip

  - https://www.sitepoint.com/quick-tip-synch-a-github-fork-via-the-command-line/

About pull reuest (PR)

  - https://help.github.com/articles/about-pull-requests/

Step-by-step

  - https://gist.github.com/colinsurprenant/9b081958b50cfecc210c
  - http://blog.scottlowe.org/2015/01/27/using-fork-branch-git-workflow/
  - https://github.com/sevntu-checkstyle/sevntu.checkstyle/wiki/Development-workflow-with-Git:-Fork,-Branching,-Commits,-and-Pull-Request
  - https://gist.github.com/Chaser324/ce0505fbed06b947d962

Comparing workflows

  - https://www.atlassian.com/git/tutorials/comparing-workflows
  - http://blogs.atlassian.com/2013/05/git-branching-and-forking-in-the-enterprise-why-fork/

Forks with feature branches

  - https://x-team.com/blog/our-git-workflow-forks-with-feature-branches/

Github workflow

  - http://hugogiraudel.com/2015/08/13/github-as-a-workflow/
  - https://github.com/servo/servo/wiki/Github-workflow

Triangle workflow

  - https://github.com/blog/2042-git-2-5-including-multiple-worktrees-and-triangular-workflows