[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue?logo=python)](https://www.python.org/downloads/release/python-3120/)
[![Framework: Textual](https://img.shields.io/badge/framework-Textual-5967FF?logo=python)](https://www.textualize.io/)
[![Pylint](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml/badge.svg?branch=master)](https://github.com/matmaer/chezmoi-mousse/actions/workflows/pylint.yml)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Linting: ruff](https://img.shields.io/badge/linting-ruff-blueviolet)](https://github.com/astral-sh/ruff)


Graphical user interface in the terminal for [chezmoi](https://github.com/twpayne/chezmoi). Built with [textual](https://github.com/Textualize/textual).

## Current Use Case

- [Chezmoi](https://www.chezmoi.io/) is installed
- Existing local `chezmoi` repository on disk (`chezmoi init` is not implemented)
- [Python 3.12+](https://www.python.org/) is installed
  (including [Textual](https://textual.textualize.io/) or run with [UV](https://docs.astral.sh/uv/getting-started/installation/))
- Can be safely tested as no write operations are enabled by default.
- The current implementation has only been used or tested with autocommit enabled.

## Available Chezmoi commands

> Enable write operations by setting an env var MOUSSE_ENABLE_CHANGES=1

> The list below is a limited subset of availabble chezmoi commands, run `chezmoi help` in your terminal to see all commands.  Commands below without a checkmark are being implemented, missing commands could be out of scope or take a while.

### Write Operations

- [x] `chezmoi add` file
- [ ] `chezmoi add` directory
- [ ] `chezmoi add --encrypt` file
- [ ] `chezmoi add --encrypt` directory
- [x] `chezmoi apply` file
- [ ] `chezmoi apply` directory
- [x] `chezmoi destroy` file
- [ ] `chezmoi destroy` directory
- [ ] `chezmoi edit`
- [x] `chezmoi forget` file
- [ ] `chezmoi forget` directory
- [ ] `chezoi generate`
- [ ] `chezmoi init`
- [ ] `chezmoi purge`
- [x] `chezmoi re-add` file
- [ ] `chezmoi re-add` directory

### Read Operations

- [x] `chezmoi cat`
- [x] `chezmoi cat-config`
- [x] `chezmoi dump-config`
- [x] `chezmoi data`
- [x] `chezmoi diff`
- [x] `chezmoi doctor`
- [x] `chezmoi git log`
- [x] `chezmoi ignored`
- [x] `chezmoi managed`
- [x] `chezmoi source-dir`
- [x] `chezmoi status`
- [x] `chezmoi unmanaged`
- [ ] `chezmoi verify`

### Other Operations

- [ ] `chezmoi archive`


### Implemented configuration options

**Legend:**

- :green_circle: Follow user configuration or chezmoi defaults
- :green_square: Provided by this app
- :negative_squared_cross_mark: Not in scope
- :bulb: Follows user config with warning
- :black_circle: Under development, help wanted or to be documented

Top level

- :green_circle: cacheDir
- :green_square: color
- :green_circle: data
- :green_circle: destDir
- :black_circle: encryption
- :black_circle: env
- :green_circle: format
- :green_square: interactive
- :negative_squared_cross_mark: mode (only file mode is supported)
- :green_square: pager
- :green_square: pagerArgs
- :black_circle: persistentState
- :green_square: progress
- :black_circle: scriptEnv
- :black_circle: scriptTempDir
- :green_circle: sourceDir
- :green_circle: tempDir
- :green_circle: umask
- :black_circle: useBuiltinAge
- :green_circle: useBuiltinGit (`chezmoi git` is used to render any git related output)
- :green_square: verbose
- :black_circle: workingTree

add
- :black_circle: add.encrypt
- :black_circle: add.secrets
- :black_circle: add.templateSymlinks

age
- :black_circle: age.args
- :black_circle: age.command
- :black_circle: age.identities
- :black_circle: age.identity
- :black_circle: age.passphrase
- :black_circle: age.recipient
- :black_circle: age.recipients
- :black_circle: age.recipientsFile
- :black_circle: age.recipientsFiles
- :black_circle: age.suffix
- :black_circle: age.symmetric

awsSecretsManager
- :black_circle: awsSecretsManager.profile
- :black_circle: awsSecretsManager.region

azureKeyVault
- :black_circle: azureKeyVault.defaultVault

bitwarden
- :black_circle: bitwarden.command
- :black_circle: bitwarden.unlock

bitwardenSecrets
- :black_circle: bitwardenSecrets.command

cd
- :black_circle: cd.args
- :black_circle: cd.command

dashlane
- :black_circle: dashlane.args
- :black_circle: dashlane.command

diff
- :green_square: diff.args
- :green_circle: diff.command (`chezmoi diff` is used to render any diff related output)
- :green_square: diff.exclude
- :green_square: diff.pager
- :green_square: diff.pagerArgs
- :green_square: diff.reverse
- :black_circle: diff.scriptContents

doppler
- :black_circle: doppler.args
- :black_circle: doppler.command
- :black_circle: doppler.config
- :black_circle: doppler.project

edit
- :black_circle: edit.apply
- :black_circle: edit.args
- :black_circle: edit.command
- :black_circle: edit.hardlink
- :black_circle: edit.minDuration
- :black_circle: edit.watch

ejson
- :black_circle: ejson.key
- :black_circle: ejson.keyDir

git
- :black_circle: git.autoAdd
- :bulb: git.autoCommit
- :bulb: git.autoPush
- :large_blue_diamond: git.command
- :green_circle: git.commitMessageTemplate
- :green_circle: git.commitMessageTemplateFile
- :black_circle: git.lfs

gitHub
- :black_circle: gitHub.refreshPeriod

gopass
- :black_circle: gopass.command
- :black_circle: gopass.mode

gpg
- :black_circle: gpg.args
- :black_circle: gpg.command
- :black_circle: gpg.recipient
- :black_circle: gpg.recipients
- :black_circle: gpg.suffix
- :black_circle: gpg.symmetric

hooks
- :black_circle: hooks.command.post.args
- :black_circle: hooks.command.post.command
- :black_circle: hooks.command.pre.args
- :black_circle: hooks.command.pre.command

interpreters
- :black_circle: interpreters.extension.args
- :black_circle: interpreters.extension.command

keepassxc
- :black_circle: keepassxc.args
- :black_circle: keepassxc.command
- :black_circle: keepassxc.database
- :black_circle: keepassxc.mode
- :black_circle: keepassxc.prompt

keeper
- :black_circle: keeper.args
- :black_circle: keeper.command

lastpass
- :black_circle: lastpass.command

merge
- :black_circle: merge.args
- :black_circle: merge.command

onepassword
- :black_circle: onepassword.cache
- :black_circle: onepassword.command
- :black_circle: onepassword.mode
- :black_circle: onepassword.prompt

pass
- :black_circle: pass.command

passhole
- :black_circle: passhole.args
- :black_circle: passhole.command
- :black_circle: passhole.prompt

pinentry
- :black_circle: pinentry.args
- :black_circle: pinentry.command
- :black_circle: pinentry.options

rbw
- :black_circle: rbw.command

secret
- :black_circle: secret.args
- :black_circle: secret.command

status
- :green_square: status.pathStyle
- :green_square: status.exclude

template
- :black_circle: template.options

textconv
- :black_circle: textconv

update
- :black_circle: update.apply
- :black_circle: update.args
- :black_circle: update.command
- :black_circle: update.recurseSubmodules

vault
- :black_circle: vault.command

verify
- :black_circle: verify.exclude

warnings
- :black_circle: warnings


## Start

> Don't run the python command in a `chezmoi cd` invoked shell, unless you want to test.

Required: `chezmoi` command available and existing `chezmoi` repository.

Clone repo and cd into the `src` directory of the cloned repo.

Then run `python -m chezmoi_mousse`

If you don't have `textual` installed but the `uv` command is available:
`uv run --with textual -m chezmoi_mousse`


- [x] python -m chezmoi_mousse (Python 3.13 with the latest `textual` version installed)
- [x] uv run --with textual -m chezmoi_mousse
- [x] Windows
  - [ ] app store
  - [ ] signed executable
  - [x] unpackaged
- [x] Apple
  - [ ] app store
  - [ ] signed executable
  - [x] unpackaged
- [x] Linux
  - [ ] AppImage
  - [ ] briefcase
  - [ ] flatpak
  - [ ] public key list signed executable
  - [ ] snap
  - [x] unpackaged
