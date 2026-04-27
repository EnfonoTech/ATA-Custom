<template>
	<div class="cinema-shell">
		<!-- Animated cinematic background -->
		<div class="cinema-bg" aria-hidden="true">
			<div class="cinema-orb orb-1"></div>
			<div class="cinema-orb orb-2"></div>
			<div class="cinema-orb orb-3"></div>
			<div class="cinema-grid"></div>
			<div class="cinema-noise"></div>
			<div class="cinema-vignette"></div>
		</div>

		<!-- Toast -->
		<transition name="slide-toast">
			<div v-if="error" class="fixed bottom-6 right-6 z-50">
				<div
					class="flex max-w-sm items-start gap-3 rounded-xl border border-red-500/30 bg-red-950/70 px-4 py-3 text-sm text-red-100 shadow-2xl backdrop-blur-md"
					role="alert"
				>
					<svg class="mt-0.5 h-4 w-4 shrink-0 text-red-300" viewBox="0 0 16 16" fill="currentColor">
						<path
							d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"
						/>
					</svg>
					<p class="flex-1 font-medium">{{ error }}</p>
					<button
						class="ml-2 flex h-5 w-5 items-center justify-center rounded text-red-300 transition hover:bg-red-900/40 hover:text-red-100"
						@click="error = ''"
					>
						✕
					</button>
				</div>
			</div>
		</transition>

		<!-- Two-pane stage -->
		<div class="relative z-10 grid min-h-screen grid-cols-1 lg:grid-cols-[1.1fr_1fr]">
			<!-- Left: cinematic poster -->
			<aside class="relative hidden flex-col justify-between p-12 text-white lg:flex">
				<div class="flex items-center gap-3">
					<div class="cinema-logo">
						<lucide-package class="h-5 w-5" />
					</div>
					<div>
						<p class="text-xs uppercase tracking-[0.32em] text-white/60">Portal</p>
						<p class="text-base font-semibold">Projects · Files · Audit</p>
					</div>
				</div>

				<div class="max-w-xl space-y-5">
					<p class="cinema-eyebrow">
						<span class="cinema-eyebrow-dot"></span>
						Welcome back
					</p>
					<h2 class="cinema-title">
						Where projects, <br />
						drawings & people <br />
						<span class="cinema-title-accent">come into focus.</span>
					</h2>
					<p class="text-base leading-relaxed text-white/70">
						Browse the standard folder structure, share work with the right collaborators, and
						keep every revision audit-ready — all from one elegant workspace.
					</p>
					<div class="cinema-marquee">
						<div class="cinema-marquee-track">
							<span>· Folder standards</span>
							<span>· File sharing</span>
							<span>· Revision history</span>
							<span>· Cinematic UI</span>
							<span>· Folder standards</span>
							<span>· File sharing</span>
							<span>· Revision history</span>
							<span>· Cinematic UI</span>
						</div>
					</div>
				</div>

				<p class="text-xs text-white/40">
					© {{ new Date().getFullYear() }} Portal · Authorised personnel only
				</p>
			</aside>

			<!-- Right: glass login card -->
			<main class="relative flex items-center justify-center p-6 sm:p-12">
				<div class="cinema-card portal-anim-in">
					<div class="mb-7 text-center lg:hidden">
						<div class="cinema-logo mx-auto mb-3">
							<lucide-package class="h-5 w-5" />
						</div>
						<h1 class="text-xl font-semibold tracking-tight text-white">Portal</h1>
					</div>

					<div class="mb-6">
						<p class="text-[11px] font-semibold uppercase tracking-[0.18em] text-white/50">
							Sign in
						</p>
						<h1 class="mt-1 text-2xl font-semibold tracking-tight text-white">
							Welcome back
						</h1>
						<p class="mt-1 text-sm text-white/60">
							Use a portal-enabled user (Projects User / Manager) or anyone listed on a Project.
						</p>
					</div>

					<form class="space-y-5" @submit.prevent="handleLogin">
						<div>
							<label class="cinema-label">Email</label>
							<div class="relative">
								<svg class="cinema-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
									<rect x="3" y="5" width="18" height="14" rx="2" />
									<path d="M3 7l9 6 9-6" />
								</svg>
								<input
									v-model="email"
									type="email"
									autocomplete="email"
									placeholder="name@company.com"
									class="cinema-input"
								/>
							</div>
						</div>

						<div>
							<div class="mb-1.5 flex items-center justify-between">
								<label class="cinema-label">Password</label>
								<a
									:href="`/login#forgot`"
									class="text-xs font-medium text-white/60 transition hover:text-white"
								>
									Forgot?
								</a>
							</div>
							<div class="relative">
								<svg class="cinema-input-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.7" stroke-linecap="round" stroke-linejoin="round">
									<rect x="4" y="11" width="16" height="10" rx="2" />
									<path d="M8 11V7a4 4 0 1 1 8 0v4" />
								</svg>
								<input
									v-model="password"
									:type="showPassword ? 'text' : 'password'"
									autocomplete="current-password"
									placeholder="••••••••"
									class="cinema-input pr-10"
									@keyup.enter="handleLogin"
								/>
								<button
									type="button"
									class="absolute right-2 top-1/2 -translate-y-1/2 rounded-md p-1.5 text-white/50 transition hover:bg-white/5 hover:text-white"
									@click="showPassword = !showPassword"
									:aria-label="showPassword ? 'Hide password' : 'Show password'"
								>
									<svg v-if="!showPassword" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
										<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z" />
										<circle cx="12" cy="12" r="3" />
									</svg>
									<svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
										<path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a19.79 19.79 0 0 1 5.06-5.94" />
										<path d="M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 7 11 7a19.79 19.79 0 0 1-3.17 4.19" />
										<path d="M14.12 14.12a3 3 0 1 1-4.24-4.24" />
										<path d="M1 1l22 22" />
									</svg>
								</button>
							</div>
						</div>

						<button type="submit" class="cinema-cta" :disabled="loading">
							<span v-if="!loading">Sign in</span>
							<span v-else class="flex items-center justify-center gap-2">
								<span class="h-3 w-3 animate-spin rounded-full border-2 border-white border-t-transparent"></span>
								Signing in…
							</span>
						</button>
					</form>

					<p class="mt-7 text-center text-[11px] text-white/40">
						Sessions are protected by Frappe / ERPNext authentication.
					</p>
				</div>
			</main>
		</div>
	</div>
</template>

<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { call, ensureCsrfReady } from "@/api";

const router = useRouter();

const email = ref("");
const password = ref("");
const loading = ref(false);
const error = ref("");
const showPassword = ref(false);

const showToast = (message) => {
	error.value = message;
	setTimeout(() => (error.value = ""), 4000);
};

const handleLogin = async () => {
	if (!email.value.trim() || !password.value) {
		showToast("Please enter email and password.");
		return;
	}
	loading.value = true;
	error.value = "";
	try {
		const res = await fetch("/api/method/login", {
			method: "POST",
			credentials: "include",
			headers: { "Content-Type": "application/json" },
			body: JSON.stringify({ usr: email.value, pwd: password.value }),
		});
		const data = await res.json();
		if (!res.ok) {
			showToast(getFrappeError(data));
			return;
		}
		// Frappe issues a new CSRF token on successful login; prime the cache before
		// any subsequent POST calls so the user doesn't see CSRFTokenError on the next click.
		await ensureCsrfReady();
		const portalCheck = await call({ method: "portal_app.api.auth.check_portal_access" });
		if (!portalCheck?.valid) {
			showToast(
				portalCheck?.guest
					? "Sign-in did not keep a session (cookies blocked or wrong site URL). Check browser settings."
					: "You do not have access to the project portal.",
			);
			return;
		}
		try {
			const me = await call({ method: "portal_app.api.profile.get_my_profile" });
			localStorage.setItem("full_name", me?.full_name || me?.name || email.value);
			if (me?.user_image != null) localStorage.setItem("profile_image", me.user_image || "");
		} catch {
			localStorage.setItem("full_name", data.full_name || email.value);
		}
		await router.push("/dashboard");
	} catch (err) {
		showToast("Server error. Please try again.");
	} finally {
		loading.value = false;
	}
};

const getFrappeError = (data) => {
	if (data?._server_messages) {
		const messages = JSON.parse(data._server_messages);
		if (messages.length) {
			try {
				return JSON.parse(messages[0]).message;
			} catch {
				return messages[0];
			}
		}
	}
	return data?.message || data?.exception || "Something went wrong";
};
</script>

<style scoped>
.cinema-shell {
	position: relative;
	min-height: 100vh;
	overflow: hidden;
	background: #05060d;
	color: #fff;
	font-family: inherit;
	isolation: isolate;
}

.cinema-bg {
	position: absolute;
	inset: 0;
	z-index: 0;
	overflow: hidden;
}

.cinema-orb {
	position: absolute;
	border-radius: 9999px;
	filter: blur(90px);
	opacity: 0.7;
	animation: cinema-float 22s ease-in-out infinite;
	will-change: transform;
}
.orb-1 {
	width: 700px;
	height: 700px;
	left: -180px;
	top: -160px;
	background: radial-gradient(circle, #6366f1 0%, transparent 70%);
}
.orb-2 {
	width: 520px;
	height: 520px;
	right: -120px;
	top: 40%;
	background: radial-gradient(circle, #ec4899 0%, transparent 70%);
	animation-delay: -7s;
	animation-duration: 28s;
}
.orb-3 {
	width: 600px;
	height: 600px;
	left: 32%;
	bottom: -220px;
	background: radial-gradient(circle, #06b6d4 0%, transparent 70%);
	animation-delay: -14s;
	animation-duration: 26s;
}

@keyframes cinema-float {
	0%,
	100% {
		transform: translate3d(0, 0, 0) scale(1);
	}
	33% {
		transform: translate3d(40px, -30px, 0) scale(1.06);
	}
	66% {
		transform: translate3d(-30px, 40px, 0) scale(0.95);
	}
}

.cinema-grid {
	position: absolute;
	inset: 0;
	background-image:
		linear-gradient(rgba(255, 255, 255, 0.04) 1px, transparent 1px),
		linear-gradient(90deg, rgba(255, 255, 255, 0.04) 1px, transparent 1px);
	background-size: 56px 56px;
	mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
	-webkit-mask-image: radial-gradient(ellipse at center, black 30%, transparent 80%);
}

.cinema-noise {
	position: absolute;
	inset: 0;
	opacity: 0.18;
	mix-blend-mode: overlay;
	background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='160' height='160'><filter id='n'><feTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='2' stitchTiles='stitch'/><feColorMatrix values='0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 0.55 0'/></filter><rect width='100%' height='100%' filter='url(%23n)'/></svg>");
}

.cinema-vignette {
	position: absolute;
	inset: 0;
	background: radial-gradient(ellipse at center, transparent 40%, rgba(0, 0, 0, 0.55) 100%);
	pointer-events: none;
}

/* Logo + eyebrow */
.cinema-logo {
	display: inline-flex;
	height: 38px;
	width: 38px;
	align-items: center;
	justify-content: center;
	border-radius: 12px;
	color: #fff;
	background: linear-gradient(135deg, #6366f1 0%, #ec4899 50%, #06b6d4 100%);
	box-shadow: 0 12px 40px -10px rgba(99, 102, 241, 0.5), inset 0 0 0 1px rgba(255, 255, 255, 0.18);
}

.cinema-eyebrow {
	display: inline-flex;
	align-items: center;
	gap: 0.5rem;
	font-size: 11px;
	font-weight: 600;
	letter-spacing: 0.32em;
	text-transform: uppercase;
	color: rgba(255, 255, 255, 0.7);
}
.cinema-eyebrow-dot {
	display: inline-block;
	width: 8px;
	height: 8px;
	border-radius: 9999px;
	background: linear-gradient(135deg, #ec4899, #06b6d4);
	box-shadow: 0 0 12px rgba(236, 72, 153, 0.7);
}

.cinema-title {
	font-size: clamp(2.6rem, 4.5vw, 3.6rem);
	line-height: 1.04;
	font-weight: 700;
	letter-spacing: -0.02em;
}
.cinema-title-accent {
	background: linear-gradient(120deg, #a5b4fc 0%, #f0abfc 50%, #67e8f9 100%);
	-webkit-background-clip: text;
	background-clip: text;
	color: transparent;
}

.cinema-marquee {
	margin-top: 1.25rem;
	overflow: hidden;
	mask-image: linear-gradient(to right, transparent, black 8%, black 92%, transparent);
	-webkit-mask-image: linear-gradient(to right, transparent, black 8%, black 92%, transparent);
}
.cinema-marquee-track {
	display: inline-flex;
	gap: 2rem;
	white-space: nowrap;
	color: rgba(255, 255, 255, 0.5);
	font-size: 0.78rem;
	letter-spacing: 0.18em;
	text-transform: uppercase;
	animation: cinema-marquee 24s linear infinite;
}
@keyframes cinema-marquee {
	from {
		transform: translateX(0);
	}
	to {
		transform: translateX(-50%);
	}
}

/* Glass card */
.cinema-card {
	width: 100%;
	max-width: 460px;
	border-radius: 26px;
	padding: 2.25rem 2.25rem 2rem;
	background: linear-gradient(135deg, rgba(255, 255, 255, 0.07) 0%, rgba(255, 255, 255, 0.025) 100%);
	border: 1px solid rgba(255, 255, 255, 0.12);
	box-shadow:
		0 30px 80px -30px rgba(0, 0, 0, 0.7),
		0 0 0 1px rgba(255, 255, 255, 0.04),
		inset 0 1px 0 rgba(255, 255, 255, 0.06);
	backdrop-filter: blur(26px) saturate(160%);
	-webkit-backdrop-filter: blur(26px) saturate(160%);
}

/* Inputs */
.cinema-label {
	display: block;
	margin-bottom: 0.4rem;
	font-size: 11px;
	font-weight: 600;
	letter-spacing: 0.16em;
	text-transform: uppercase;
	color: rgba(255, 255, 255, 0.55);
}
.cinema-input {
	width: 100%;
	padding: 0.78rem 1rem 0.78rem 2.5rem;
	border-radius: 14px;
	background: rgba(255, 255, 255, 0.04);
	border: 1px solid rgba(255, 255, 255, 0.12);
	color: #fff;
	font-size: 0.95rem;
	transition: border-color 0.2s ease, background 0.2s ease, box-shadow 0.2s ease;
}
.cinema-input::placeholder {
	color: rgba(255, 255, 255, 0.35);
}
.cinema-input:focus {
	outline: none;
	border-color: rgba(165, 180, 252, 0.6);
	background: rgba(255, 255, 255, 0.07);
	box-shadow: 0 0 0 4px rgba(99, 102, 241, 0.18);
}
.cinema-input-icon {
	position: absolute;
	left: 0.85rem;
	top: 50%;
	transform: translateY(-50%);
	width: 16px;
	height: 16px;
	color: rgba(255, 255, 255, 0.5);
	pointer-events: none;
}

/* CTA */
.cinema-cta {
	width: 100%;
	padding: 0.85rem 1rem;
	border-radius: 14px;
	font-weight: 600;
	letter-spacing: 0.02em;
	color: #fff;
	background: linear-gradient(135deg, #6366f1 0%, #a855f7 50%, #ec4899 100%);
	border: 1px solid rgba(255, 255, 255, 0.18);
	box-shadow:
		0 16px 30px -10px rgba(168, 85, 247, 0.55),
		inset 0 1px 0 rgba(255, 255, 255, 0.18);
	transition: transform 0.15s ease, box-shadow 0.2s ease, filter 0.2s ease;
	cursor: pointer;
}
.cinema-cta:hover {
	transform: translateY(-1px);
	filter: brightness(1.08);
}
.cinema-cta:active {
	transform: translateY(1px);
}
.cinema-cta:disabled {
	cursor: progress;
	filter: brightness(0.85) saturate(0.9);
}

/* Toast keeps original transition */
.slide-toast-enter-active,
.slide-toast-leave-active {
	transition: all 0.35s ease;
}
.slide-toast-enter-from {
	opacity: 0;
	transform: translateX(100%);
}
.slide-toast-leave-to {
	opacity: 0;
	transform: translateX(100%);
}

@media (prefers-reduced-motion: reduce) {
	.cinema-orb,
	.cinema-marquee-track {
		animation: none;
	}
}
</style>
