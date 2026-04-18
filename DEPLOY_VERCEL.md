# Deploying to Vercel (`platform` app)

## What went wrong

`cd platform && npm ci` fails with **`No such file or directory`** when either:

1. The **`platform/`** folder is **not on the Git branch** Vercel builds (e.g. not pushed to `main`), or  
2. **Root Directory** in Vercel is wrong and custom install commands assume a path that does not exist in the clone.

## Fix A — Recommended (simplest)

1. In Vercel: **Project → Settings → General**
2. Set **Root Directory** to: `platform`
3. Clear **overrides** so defaults apply, or set explicitly:
   - **Install Command:** `npm ci`  
   - **Build Command:** `npm run build`  
4. Remove any install command that starts with `cd platform &&` — it is **redundant** when Root Directory is already `platform`.

`platform/vercel.json` is used automatically when the project root is `platform`.

## Fix B — Build from repository root

If you **must** keep Root Directory as **`.`** (monorepo root), this repo includes a **root `vercel.json`** that runs:

- `npm ci --prefix platform`
- `npm run build --prefix platform`

No `cd` is used; `npm --prefix` targets the `platform` package. **The `platform` directory must still exist** in the GitHub repo on the deployed branch.

1. Confirm on GitHub: `platform/package.json` exists on `main` (or your production branch).  
2. In Vercel, **remove** custom **Install Command** / **Build Command** overrides if they still use `cd platform`, so the root `vercel.json` is applied — or align them with the same `--prefix` commands.

## After changing settings

Redeploy (Redeploy / clear cache) so the new root directory and commands take effect.

## Data on server

The app reads CSVs under `platform/data_*` at runtime. Ensure those folders are committed or provided via your deployment process (see `platform` README / data pipeline).
