---
name: sidequest-admin-access
description: Use when creating, unblocking, or verifying a SideQuest admin user or the SideQuest admin login path, including Supabase Auth user setup, admin role checks, ADMIN_ALLOWED_EMAILS in Vercel, admin-web redeploy, and live /login to /admin verification. This is for SideQuest admin access only, not general Supabase or Vercel work.
---

# SideQuest Admin Access

Provision or verify SideQuest admin access end to end. The key rule is that Supabase Auth, SideQuest admin roles, Vercel allowlist, deployment, and the live login path must all agree before the admin is actually ready.

Operations that create users, set passwords, modify Vercel env vars, or redeploy require explicit user intent. Do not invent credentials or print secrets.

## When To Use

- The user asks to create or unblock a SideQuest admin user.
- The user asks whether the SideQuest admin panel/login is live.
- The user reports that an admin email/password exists but cannot enter `/admin`.
- The task mentions `ADMIN_ALLOWED_EMAILS`, `sidequest-admin-web`, `sidequest.dautia.com/login`, Supabase Auth, or SideQuest admin roles.

Do not use this for normal app auth bugs, iOS session issues, non-admin users, unrelated Supabase schema work, or generic Vercel deployment tasks.

## Source Order

1. Resolve the SideQuest Git root from the current checkout or a user-provided path. Confirm it with `delivery.yaml` and the `sidequest` remote before acting.
2. Read only the relevant docs/code for the target access path:
   - `docs/arquitecura.md`
   - `docs/checklist_infra.md`
   - `sidequest-codebase/admin-web`
   - relevant Supabase migrations or tests when role shape is unclear
3. Prefer live source systems for current state: Supabase, Vercel, and the deployed admin URL.

## Workflow

1. Confirm target and credentials.
   - Determine whether the task targets staging, production, or the live alias.
   - Use the email/password supplied by the user or ask for the missing credential input.
   - Do not echo passwords in logs, docs, or final responses.

2. Verify the live admin entrypoint.
   - Current known entrypoint is usually `https://sidequest.dautia.com/login`, with `/admin` behind auth.
   - Confirm this from docs or Vercel before relying on it if the environment may have changed.
   - Check that `/login` renders the expected password form and does not show stale OTP or magic-link UX when the task is about current admin login.

3. Configure Supabase Auth.
   - Identify the correct Supabase project from repo env, Vercel env, or Supabase connector state.
   - Create or update the Auth user only if explicitly requested.
   - Confirm email when appropriate and set the requested password.
   - Ensure the app-level admin record exists and is active, typically in `sidequest.admin_roles` with `role = admin` and `is_active = true`.

4. Prove Supabase sign-in before touching Vercel.
   - Sign in with the publishable key or app-equivalent client path.
   - Do not use a service-role-only check as proof that the user can log in.

5. Sync Vercel allowlist.
   - Inspect `ADMIN_ALLOWED_EMAILS` for the `sidequest-admin-web` project and target environment.
   - If the email is missing and the user asked to enable access, update the allowlist without removing existing admins.
   - Redeploy or refresh the deployment as needed so the env var is active.

6. Verify the live path.
   - Use Browser, Playwright, or an HTTP/server-action smoke that exercises the real `/login` form.
   - Successful proof is a real login response redirecting to `/admin` and a follow-up `/admin` request returning `200` with session cookies.
   - If using Browser, confirm the visible page lands inside the admin console.

## Output

Report:

- target environment and live URL
- whether the Supabase Auth user exists or was updated
- whether the admin role row is active
- whether `ADMIN_ALLOWED_EMAILS` contained the email or was updated
- whether Vercel was redeployed or already current
- final `/login` to `/admin` verification result

Never include passwords, service-role keys, session cookies, or complete env var values.

## Pitfalls

- Creating the Supabase Auth user is not enough if `ADMIN_ALLOWED_EMAILS` is stale.
- A service-role lookup is not proof of operator login; verify with the publishable key or the live form.
- Do not claim access is ready until the live `/login` to `/admin` path is proven.
- If a quick Node helper mixes `require()` with top-level `await`, wrap it in an async IIFE or use a consistent module style instead of debugging Supabase first.
