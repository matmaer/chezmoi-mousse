# Command outputs prior to running `chezmoi init`

> Random test in the context of implementing the app's init screen.

## Fedora Linux 42 (Workstation Edition)

### `chezmoi doctor` output

> exit code 1

```yaml
RESULT    CHECK                       MESSAGE
ok        version                     v2.63.1, commit c3ab5f0ba37b2ba58b534eacc65a9a4e8ed75e86, built at 2025-09-08T00:00:00Z, built by Fedora
warning   latest-version              v2.66.1
ok        os-arch                     linux/amd64 (Fedora Linux 42 (Workstation Edition))
ok        uname                       Linux fedora 6.14.0-63.fc42.x86_64 #1 SMP PREEMPT_DYNAMIC Mon Mar 24 19:53:37 UTC 2025 x86_64 GNU/Linux
ok        go-version                  go1.24.6 (gc)
ok        executable                  /usr/bin/chezmoi
info      config-file                 ~/.config/chezmoi/chezmoi.toml: not found
error     source-dir                  open ~/.local/share/chezmoi: no such file or directory
ok        suspicious-entries          ~/.local/share/chezmoi: no such file or directory
error     working-tree                open ~/.local/share/chezmoi: no such file or directory
ok        dest-dir                    ~ is a directory
ok        umask                       022
ok        cd-command                  found /bin/bash
ok        cd-args                     /bin/bash
info      diff-command                not set
ok        edit-command                found /usr/bin/nano
ok        edit-args                   /usr/bin/nano
ok        git-command                 found /usr/bin/git, version 2.49.0
warning   merge-command               vimdiff not found in $PATH
ok        shell-command               found /bin/bash
ok        shell-args                  /bin/bash
info      age-command                 age not found in $PATH
ok        gpg-command                 found /usr/bin/gpg, version 2.4.7
info      pinentry-command            not set
info      1password-command           op not found in $PATH
info      bitwarden-command           bw not found in $PATH
info      bitwarden-secrets-command   bws not found in $PATH
info      dashlane-command            dcli not found in $PATH
info      doppler-command             doppler not found in $PATH
info      gopass-command              gopass not found in $PATH
info      keepassxc-command           keepassxc-cli not found in $PATH
info      keepassxc-db                not set
info      keeper-command              keeper not found in $PATH
info      lastpass-command            lpass not found in $PATH
info      pass-command                pass not found in $PATH
info      passhole-command            ph not found in $PATH
info      rbw-command                 rbw not found in $PATH
info      vault-command               vault not found in $PATH
info      vlt-command                 vlt not found in $PATH
info      secret-command              not set
```

### `chezmoi dump-config` output

> Exit code 0

```json
{
  "cacheDir": "/home/tester/.cache/chezmoi",
  "color": "auto",
  "data": null,
  "env": null,
  "format": "json",
  "destDir": "/home/tester",
  "gitHub": {
    "refreshPeriod": 60000000000
  },
  "hooks": null,
  "interactive": false,
  "interpreters": {},
  "mode": "file",
  "pager": "",
  "pagerArgs": null,
  "persistentState": "",
  "pinentry": {
    "command": "",
    "args": null,
    "options": [
      "allow-external-password-cache"
    ]
  },
  "progress": "auto",
  "safe": true,
  "scriptEnv": null,
  "scriptTempDir": "",
  "sourceDir": "/home/tester/.local/share/chezmoi",
  "tempDir": "/tmp",
  "template": {
    "options": [
      "missingkey=error"
    ]
  },
  "textConv": null,
  "umask": 18,
  "useBuiltinAge": "auto",
  "useBuiltinGit": "auto",
  "verbose": false,
  "warnings": {
    "configFileTemplateHasChanged": true
  },
  "workingTree": "/home/tester/.local/share/chezmoi",
  "awsSecretsManager": {
    "region": "",
    "profile": ""
  },
  "azureKeyVault": {
    "defaultVault": ""
  },
  "bitwarden": {
    "command": "bw"
  },
  "bitwardenSecrets": {
    "command": "bws"
  },
  "dashlane": {
    "command": "dcli",
    "args": null
  },
  "doppler": {
    "command": "doppler",
    "args": null,
    "project": "",
    "config": ""
  },
  "ejson": {
    "keyDir": "/opt/ejson/keys",
    "key": ""
  },
  "gopass": {
    "command": "gopass",
    "mode": ""
  },
  "hcpVaultSecrets": {
    "command": "vlt",
    "args": null,
    "applicationName": "",
    "organizationId": "",
    "projectId": ""
  },
  "keepassxc": {
    "command": "keepassxc-cli",
    "database": "",
    "mode": "cache-password",
    "args": null,
    "prompt": true
  },
  "keeper": {
    "command": "keeper",
    "args": null
  },
  "lastpass": {
    "command": "lpass"
  },
  "onepassword": {
    "command": "op",
    "prompt": true,
    "mode": "account"
  },
  "pass": {
    "command": "pass"
  },
  "passhole": {
    "command": "ph",
    "args": null,
    "prompt": true
  },
  "rbw": {
    "command": "rbw"
  },
  "secret": {
    "command": "",
    "args": null
  },
  "vault": {
    "command": "vault"
  },
  "encryption": "",
  "age": {
    "useBuiltin": false,
    "command": "age",
    "args": null,
    "identity": "",
    "identities": null,
    "passphrase": false,
    "recipient": "",
    "recipients": null,
    "recipientsFile": "",
    "recipientsFiles": null,
    "suffix": ".age",
    "symmetric": false
  },
  "gpg": {
    "command": "gpg",
    "args": null,
    "recipient": "",
    "recipients": null,
    "symmetric": false,
    "suffix": ".asc"
  },
  "add": {
    "encrypt": false,
    "secrets": "warning",
    "templateSymlinks": false
  },
  "cd": {
    "command": "",
    "args": null
  },
  "completion": {
    "custom": false
  },
  "diff": {
    "command": "",
    "args": null,
    "exclude": [],
    "pager": "\u0000",
    "pagerArgs": null,
    "reverse": false,
    "scriptContents": true
  },
  "edit": {
    "command": "",
    "args": null,
    "hardlink": true,
    "minDuration": 1000000000,
    "watch": false,
    "apply": false
  },
  "git": {
    "command": "git",
    "autoadd": false,
    "autocommit": false,
    "autopush": false,
    "commitMessageTemplate": "",
    "commitMessageTemplateFile": "",
    "lfs": false
  },
  "merge": {
    "command": "vimdiff",
    "args": null
  },
  "status": {
    "exclude": [],
    "pathStyle": "relative"
  },
  "update": {
    "command": "",
    "args": null,
    "apply": true,
    "recurseSubmodules": true
  },
  "verify": {
    "exclude": []
  }
}
```

### `chezmoi data` output

> Exit code 0

```json
{
  "chezmoi": {
    "arch": "amd64",
    "args": [
      "chezmoi",
      "data"
    ],
    "cacheDir": "/home/tester/.cache/chezmoi",
    "command": "data",
    "commandDir": "/home/tester",
    "config": {
      "add": {
        "encrypt": false,
        "secrets": "warning",
        "templateSymlinks": false
      },
      "age": {
        "args": null,
        "command": "age",
        "identities": null,
        "identity": "",
        "passphrase": false,
        "recipient": "",
        "recipients": null,
        "recipientsFile": "",
        "recipientsFiles": null,
        "suffix": ".age",
        "symmetric": false,
        "useBuiltin": false
      },
      "awsSecretsManager": {
        "profile": "",
        "region": ""
      },
      "azureKeyVault": {
        "defaultVault": ""
      },
      "bitwarden": {
        "command": "bw"
      },
      "bitwardenSecrets": {
        "command": "bws"
      },
      "cacheDir": "/home/tester/.cache/chezmoi",
      "cd": {
        "args": null,
        "command": ""
      },
      "color": "auto",
      "completion": {
        "custom": false
      },
      "dashlane": {
        "args": null,
        "command": "dcli"
      },
      "data": null,
      "destDir": "/home/tester",
      "diff": {
        "args": null,
        "command": "",
        "exclude": [],
        "pager": "",
        "pagerArgs": null,
        "reverse": false,
        "scriptContents": true
      },
      "doppler": {
        "args": null,
        "command": "doppler",
        "config": "",
        "project": ""
      },
      "edit": {
        "apply": false,
        "args": null,
        "command": "",
        "hardlink": true,
        "minDuration": 1000000000,
        "watch": false
      },
      "ejson": {
        "key": "",
        "keyDir": "/opt/ejson/keys"
      },
      "encryption": "",
      "env": null,
      "format": "json",
      "git": {
        "autoadd": false,
        "autocommit": false,
        "autopush": false,
        "command": "git",
        "commitMessageTemplate": "",
        "commitMessageTemplateFile": "",
        "lfs": false
      },
      "gitHub": {
        "refreshPeriod": 60000000000
      },
      "gopass": {
        "command": "gopass",
        "mode": ""
      },
      "gpg": {
        "args": null,
        "command": "gpg",
        "recipient": "",
        "recipients": null,
        "suffix": ".asc",
        "symmetric": false
      },
      "hcpVaultSecrets": {
        "applicationName": "",
        "args": null,
        "command": "vlt",
        "organizationId": "",
        "projectId": ""
      },
      "hooks": null,
      "interactive": false,
      "interpreters": {},
      "keepassxc": {
        "args": null,
        "command": "keepassxc-cli",
        "database": "",
        "mode": "cache-password",
        "prompt": true
      },
      "keeper": {
        "args": null,
        "command": "keeper"
      },
      "lastpass": {
        "command": "lpass"
      },
      "merge": {
        "args": null,
        "command": "vimdiff"
      },
      "mode": "file",
      "onepassword": {
        "command": "op",
        "mode": "account",
        "prompt": true
      },
      "pager": "",
      "pagerArgs": null,
      "pass": {
        "command": "pass"
      },
      "passhole": {
        "args": null,
        "command": "ph",
        "prompt": true
      },
      "persistentState": "",
      "pinentry": {
        "args": null,
        "command": "",
        "options": [
          "allow-external-password-cache"
        ]
      },
      "progress": "auto",
      "rbw": {
        "command": "rbw"
      },
      "safe": true,
      "scriptEnv": null,
      "scriptTempDir": "",
      "secret": {
        "args": null,
        "command": ""
      },
      "sourceDir": "/home/tester/.local/share/chezmoi",
      "status": {
        "exclude": [],
        "pathStyle": "relative"
      },
      "tempDir": "/tmp",
      "template": {
        "options": [
          "missingkey=error"
        ]
      },
      "textConv": null,
      "umask": 18,
      "update": {
        "apply": true,
        "args": null,
        "command": "",
        "recurseSubmodules": true
      },
      "useBuiltinAge": "auto",
      "useBuiltinGit": "auto",
      "vault": {
        "command": "vault"
      },
      "verbose": false,
      "verify": {
        "exclude": []
      },
      "warnings": {
        "configFileTemplateHasChanged": true
      },
      "workingTree": "/home/tester/.local/share/chezmoi"
    },
    "configFile": "/home/tester/.config/chezmoi/chezmoi.toml",
    "destDir": "/home/tester",
    "executable": "/usr/bin/chezmoi",
    "fqdnHostname": "fedora",
    "gid": "1000",
    "group": "tester",
    "homeDir": "/home/tester",
    "hostname": "fedora",
    "kernel": {
      "osrelease": "6.14.0-63.fc42.x86_64",
      "ostype": "Linux",
      "version": "#1 SMP PREEMPT_DYNAMIC Mon Mar 24 19:53:37 UTC 2025"
    },
    "os": "linux",
    "osRelease": {
      "ansiColor": "0;38;2;60;110;180",
      "bugReportURL": "https://bugzilla.redhat.com/",
      "cpeName": "cpe:/o:fedoraproject:fedora:42",
      "defaultHostname": "fedora",
      "documentationURL": "https://docs.fedoraproject.org/en-US/fedora/f42/system-administrators-guide/",
      "homeURL": "https://fedoraproject.org/",
      "id": "fedora",
      "logo": "fedora-logo-icon",
      "name": "Fedora Linux",
      "platformID": "platform:f42",
      "prettyName": "Fedora Linux 42 (Workstation Edition)",
      "redhatBugzillaProduct": "Fedora",
      "redhatBugzillaProductVersion": "42",
      "redhatSupportProduct": "Fedora",
      "redhatSupportProductVersion": "42",
      "releaseType": "stable",
      "supportEnd": "2026-05-13",
      "supportURL": "https://ask.fedoraproject.org/",
      "variant": "Workstation Edition",
      "variantID": "workstation",
      "version": "42 (Workstation Edition)",
      "versionCodename": "",
      "versionID": "42"
    },
    "pathListSeparator": ":",
    "pathSeparator": "/",
    "sourceDir": "/home/tester/.local/share/chezmoi",
    "uid": "1000",
    "username": "tester",
    "version": {
      "builtBy": "Fedora",
      "commit": "c3ab5f0ba37b2ba58b534eacc65a9a4e8ed75e86",
      "date": "2025-09-08T00:00:00Z",
      "version": "2.63.1"
    },
    "windowsVersion": {},
    "workingTree": "/home/tester/.local/share/chezmoi"
  }
}
```

### chezmoi cat-config

> Exit code 1

chezmoi: open /home/tester/.config/chezmoi/chezmoi.toml: no such file or directory

# chezmoi status

> Exit code 1

chezmoi: stat /home/tester/.local/share/chezmoi: no such file or directory

### chezmoi ignored, chezmoi managed

> Exit code 0, no output

