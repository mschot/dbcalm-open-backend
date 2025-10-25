# Releasing DBCalm

This document explains how to create releases for the DBCalm open-source backend.

## Overview

Releases are automated through GitHub Actions. When you push a git tag, the workflow automatically:
1. Builds `.deb` packages in Ubuntu 22.04 Docker container
2. Creates a GitHub Release
3. Uploads packages with both version-specific and generic names
4. Generates release notes from git commits

## Creating a Release

### Step 1: Choose Your Version Number

DBCalm supports flexible versioning:
- **Major.Minor**: `v0.1`, `v1.0`, `v2.5` (recommended)
- **Semantic (Major.Minor.Patch)**: `v0.1.0`, `v1.2.3`
- **Pre-release**: `v0.1-beta`, `v1.0-rc.1`

### Step 2: Tag and Push

```bash
# Make sure you're on the main branch and up to date
git checkout main
git pull

# Create and push the tag
git tag v0.1
git push origin v0.1
```

That's it! The GitHub Actions workflow will automatically:
- Build the `.deb` package
- Create the release
- Upload the artifacts

### Step 3: Monitor the Build

1. Go to: https://github.com/mschot/dbcalm-open-backend/actions
2. Watch the "Release" workflow run
3. Build typically takes 5-10 minutes

### Step 4: Verify the Release

Once complete, the release will be available at:
- Release page: `https://github.com/mschot/dbcalm-open-backend/releases`
- Latest .deb: `https://github.com/mschot/dbcalm-open-backend/releases/latest/download/dbcalm_amd64.deb`
- Version-specific: `https://github.com/mschot/dbcalm-open-backend/releases/download/v0.1/dbcalm-0.1_amd64.deb`

## Release Artifacts

Each release includes the following files:

### Debian Packages
- `dbcalm-VERSION_amd64.deb` - Version-specific package (e.g., `dbcalm-0.1_amd64.deb`)
- `dbcalm_amd64.deb` - Generic name that always points to latest version

### Future: RPM Packages
When RPM support is added:
- `dbcalm-VERSION.x86_64.rpm` - Version-specific package
- `dbcalm.x86_64.rpm` - Generic name for latest

## Testing a Release Before Publishing

To test the release workflow without creating a public release:

```bash
# Create a pre-release tag
git tag v0.1-beta
git push origin v0.1-beta
```

Pre-release tags (containing `-`) are automatically marked as "pre-release" on GitHub and won't show up as the "latest" release.

## Updating an Existing Release

If you need to fix a release:

```bash
# Delete the tag locally and remotely
git tag -d v0.1
git push origin :refs/tags/v0.1

# Delete the GitHub release (via web UI or gh CLI)
gh release delete v0.1

# Create and push the corrected tag
git tag v0.1
git push origin v0.1
```

## Version Numbers in Code

The release workflow automatically updates `pyproject.toml` with the version from the git tag. You don't need to manually update version numbers before tagging.

**Before tagging:**
```toml
version="0.0.1"  # Can be any value
```

**After workflow runs with tag `v0.1`:**
The workflow temporarily updates it to `version="0.1"` for the build.

## Release Notes

Release notes are automatically generated from git commits between the previous tag and the current tag. For better release notes, write clear commit messages:

```bash
# Good commit messages
git commit -m "Add support for incremental backups"
git commit -m "Fix: Handle connection timeouts gracefully"
git commit -m "Improve backup speed by 40%"

# Less helpful commit messages
git commit -m "Fix bug"
git commit -m "Updates"
```

## Manual Release Notes

To customize release notes, edit them on GitHub after the release is created:
1. Go to: https://github.com/mschot/dbcalm-open-backend/releases
2. Click "Edit" on the release
3. Update the description
4. Click "Update release"


## Resources

- GitHub Actions workflow: `.github/workflows/release.yml`
- Build script for .deb: `build-deb.sh`
- Build script for .rpm: `build-rpm.sh` (placeholder)
- DEBIAN control files: `templates/DEBIAN/`
- RPM spec file: `templates/SPEC/dbcalm.spec` (template)
