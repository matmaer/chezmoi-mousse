# How to Remove pages-build-deployment from GitHub Actions

The `pages-build-deployment` workflow is automatically created by GitHub when GitHub Pages is enabled for a repository. To remove this workflow, you need to disable GitHub Pages.

## Steps to disable GitHub Pages:

1. Go to your repository on GitHub
2. Navigate to **Settings** tab
3. Scroll down to **Pages** section in the left sidebar
4. Under **Source**, select **"None"** to disable GitHub Pages
5. Click **Save**

## What this will do:

- The `pages-build-deployment` workflow will be automatically removed
- GitHub will stop attempting to build and deploy pages
- Any existing GitHub Pages site will become unavailable

## Background:

This repository previously had a `mkdocs.yml` file that was used to generate documentation with MkDocs. When that file was removed, GitHub Pages was left enabled but without valid source content, causing the workflow runs to fail. Disabling GitHub Pages completely resolves this issue.

## Alternative approaches:

If you want to keep GitHub Pages enabled for future use:

1. **Option 1**: Create a simple `index.html` file in the root directory with basic content
2. **Option 2**: Re-add a `mkdocs.yml` file with valid MkDocs configuration
3. **Option 3**: Switch to deploying from a specific branch like `gh-pages` instead of the root directory

Once you disable GitHub Pages following the steps above, this file can be deleted.