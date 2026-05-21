<template>
	<div class="login-shell">

		<!-- Error toast -->
		<transition name="slide-toast">
			<div v-if="error" class="fixed bottom-6 right-6 z-50">
				<div class="flex max-w-sm items-start gap-3 rounded-xl border border-red-200 bg-white px-4 py-3 text-sm text-red-700 shadow-2xl" role="alert">
					<svg class="mt-0.5 h-4 w-4 shrink-0 text-red-500" viewBox="0 0 16 16" fill="currentColor">
						<path d="M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z"/>
					</svg>
					<p class="flex-1 font-medium">{{ error }}</p>
					<button class="ml-2 flex h-5 w-5 items-center justify-center rounded text-red-400 transition hover:text-red-700" @click="error = ''">✕</button>
				</div>
			</div>
		</transition>

		<div class="login-grid">

			<!-- ── LEFT PANEL ── -->
			<aside class="left-panel">
				<!-- Decorative: building skyline -->
				<svg class="buildings-art" viewBox="0 0 700 480" preserveAspectRatio="xMidYMax meet" fill="none" aria-hidden="true">
					<!-- Building 1 – tall slim left -->
					<rect x="8" y="70" width="72" height="410" stroke="#c4a882" stroke-width="0.8"/>
					<line x1="44" y1="70" x2="44" y2="480" stroke="#c4a882" stroke-width="0.5"/>
					<line x1="8"  y1="130" x2="80" y2="130" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="8"  y1="190" x2="80" y2="190" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="8"  y1="250" x2="80" y2="250" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="8"  y1="310" x2="80" y2="310" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="8"  y1="370" x2="80" y2="370" stroke="#c4a882" stroke-width="0.4"/>
					<rect x="16" y="85"  width="16" height="22" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="48" y="85"  width="16" height="22" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="16" y="143" width="16" height="22" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="48" y="143" width="16" height="22" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="16" y="200" width="16" height="22" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="48" y="200" width="16" height="22" stroke="#c4a882" stroke-width="0.5"/>

					<!-- Building 2 – wide office block -->
					<rect x="100" y="155" width="130" height="325" stroke="#c4a882" stroke-width="0.8"/>
					<line x1="165" y1="155" x2="165" y2="480" stroke="#c4a882" stroke-width="0.5"/>
					<line x1="100" y1="210" x2="230" y2="210" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="100" y1="265" x2="230" y2="265" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="100" y1="320" x2="230" y2="320" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="100" y1="375" x2="230" y2="375" stroke="#c4a882" stroke-width="0.4"/>
					<rect x="112" y="168" width="20" height="27" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="144" y="168" width="20" height="27" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="176" y="168" width="20" height="27" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="208" y="168" width="16" height="27" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="112" y="224" width="20" height="27" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="144" y="224" width="20" height="27" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="176" y="224" width="20" height="27" stroke="#c4a882" stroke-width="0.5"/>

					<!-- Building 3 – narrow tower center -->
					<rect x="252" y="32" width="58" height="448" stroke="#c4a882" stroke-width="0.8"/>
					<line x1="281" y1="32"  x2="281" y2="480" stroke="#c4a882" stroke-width="0.5"/>
					<line x1="252" y1="90"  x2="310" y2="90"  stroke="#c4a882" stroke-width="0.4"/>
					<line x1="252" y1="150" x2="310" y2="150" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="252" y1="210" x2="310" y2="210" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="252" y1="270" x2="310" y2="270" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="252" y1="330" x2="310" y2="330" stroke="#c4a882" stroke-width="0.4"/>
					<rect x="258" y="46"  width="16" height="22" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="284" y="46"  width="16" height="22" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="258" y="103" width="16" height="22" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="284" y="103" width="16" height="22" stroke="#c4a882" stroke-width="0.5"/>

					<!-- Building 4 – stepped tower -->
					<rect x="330" y="115" width="90" height="365" stroke="#c4a882" stroke-width="0.8"/>
					<rect x="346" y="72"  width="58" height="48"  stroke="#c4a882" stroke-width="0.7"/>
					<line x1="375" y1="115" x2="375" y2="480" stroke="#c4a882" stroke-width="0.5"/>
					<line x1="330" y1="175" x2="420" y2="175" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="330" y1="235" x2="420" y2="235" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="330" y1="295" x2="420" y2="295" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="330" y1="355" x2="420" y2="355" stroke="#c4a882" stroke-width="0.4"/>
					<rect x="338" y="128" width="28" height="30" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="386" y="128" width="26" height="30" stroke="#c4a882" stroke-width="0.5"/>

					<!-- Building 5 – wide right block -->
					<rect x="440" y="190" width="115" height="290" stroke="#c4a882" stroke-width="0.8"/>
					<line x1="498" y1="190" x2="498" y2="480" stroke="#c4a882" stroke-width="0.5"/>
					<line x1="440" y1="248" x2="555" y2="248" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="440" y1="306" x2="555" y2="306" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="440" y1="364" x2="555" y2="364" stroke="#c4a882" stroke-width="0.4"/>
					<rect x="450" y="204" width="20" height="26" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="478" y="204" width="20" height="26" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="510" y="204" width="20" height="26" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="535" y="204" width="14" height="26" stroke="#c4a882" stroke-width="0.5"/>

					<!-- Building 6 – far right slim tower -->
					<rect x="585" y="88" width="56" height="392" stroke="#c4a882" stroke-width="0.8"/>
					<line x1="613" y1="88"  x2="613" y2="480" stroke="#c4a882" stroke-width="0.5"/>
					<line x1="585" y1="150" x2="641" y2="150" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="585" y1="212" x2="641" y2="212" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="585" y1="274" x2="641" y2="274" stroke="#c4a882" stroke-width="0.4"/>
					<line x1="585" y1="336" x2="641" y2="336" stroke="#c4a882" stroke-width="0.4"/>
					<rect x="591" y="102" width="14" height="20" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="617" y="102" width="14" height="20" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="591" y="162" width="14" height="20" stroke="#c4a882" stroke-width="0.5"/>
					<rect x="617" y="162" width="14" height="20" stroke="#c4a882" stroke-width="0.5"/>

					<!-- Ground -->
					<line x1="0" y1="479" x2="700" y2="479" stroke="#c4a882" stroke-width="1.2"/>
				</svg>

				<!-- Decorative: accent wave curves (theme-reactive) -->
				<svg class="waves-art" viewBox="0 0 700 160" preserveAspectRatio="none" fill="none" aria-hidden="true">
					<path d="M-10,140 C80,90  200,165 360,108 C520,52  610,120 720,88"
					      stroke="var(--portal-accent)" stroke-width="2.8" stroke-linecap="round" opacity="0.72"/>
					<path d="M-10,118 C100,72 230,148 400,90  C560,38  638,108 720,72"
					      stroke="var(--portal-accent)" stroke-width="1.8" stroke-linecap="round" opacity="0.45"/>
					<path d="M-10,155 C60,110 185,178 340,125 C490,75  575,138 720,112"
					      stroke="var(--portal-accent)" stroke-width="1.0" stroke-linecap="round" opacity="0.28"/>
				</svg>

				<!-- Logo -->
				<div class="brand-top">
					<img v-if="brandLogo" :src="brandLogo" class="h-11 w-auto object-contain" :alt="brandName || 'Logo'"/>
					<div v-else class="brand-mark" aria-hidden="true">
						<!-- Geometric lettermark inspired by AMA logo -->
						<svg viewBox="0 0 52 44" fill="currentColor" class="h-9 w-auto">
							<path d="M1,42 L9,2  L16,2  L8,42Z"/>
							<path d="M17,42 L23,13 L29,13 L23,42Z"/>
							<path d="M27,42 L33,13 L39,13 L33,42Z"/>
							<path d="M37,42 L44,2  L51,2  L44,42Z"/>
						</svg>
					</div>
					<div class="brand-text">
						<p class="brand-name-ar" v-if="!brandName">عبد المحسن الذياب وشركاه</p>
						<p class="brand-name">{{ brandName || 'ABDULMOHSIN ALTHEYAB &amp; PARTNERS' }}</p>
						<p class="brand-sub">{{ brandTagline || 'ARCHITECTS | معماريون' }}</p>
					</div>
				</div>

				<!-- Headline -->
				<div class="brand-headline">
					<h2 class="headline-title">Welcome back</h2>
					<p class="headline-sub">Sign in to your ERPNext account</p>
				</div>

				<!-- Copyright -->
				<p class="brand-copy">© {{ new Date().getFullYear() }} ATA Architects. All rights reserved.</p>
			</aside>

			<!-- ── RIGHT PANEL ── -->
			<main class="right-panel">
				<div class="login-card portal-anim-in">

					<!-- Mobile logo (shown only on small screens) -->
					<div class="mobile-logo">
						<svg viewBox="0 0 52 44" fill="currentColor" class="h-10 w-auto text-gray-900">
							<path d="M1,42 L9,2  L16,2  L8,42Z"/>
							<path d="M17,42 L23,13 L29,13 L23,42Z"/>
							<path d="M27,42 L33,13 L39,13 L33,42Z"/>
							<path d="M37,42 L44,2  L51,2  L44,42Z"/>
						</svg>
					</div>

					<!-- Card header -->
					<div class="card-header">
						<h1 class="card-title">ERP Portal</h1>
						<p class="card-sub">Please enter your credentials to continue</p>
					</div>

					<!-- Form -->
					<form class="space-y-5" @submit.prevent="handleLogin">

						<!-- Email / Username -->
						<div>
							<label class="field-label" for="login-email">Email / Username</label>
							<input
								id="login-email"
								v-model="email"
								type="text"
								autocomplete="username"
								placeholder="Enter your email or username"
								class="field-input"
							/>
						</div>

						<!-- Password -->
						<div>
							<label class="field-label" for="login-password">Password</label>
							<div class="relative">
								<input
									id="login-password"
									v-model="password"
									:type="showPassword ? 'text' : 'password'"
									autocomplete="current-password"
									placeholder="Enter your password"
									class="field-input pr-11"
									@keyup.enter="handleLogin"
								/>
								<button
									type="button"
									class="eye-btn"
									:aria-label="showPassword ? 'Hide password' : 'Show password'"
									@click="showPassword = !showPassword"
								>
									<svg v-if="!showPassword" class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
										<path d="M1 12s4-7 11-7 11 7 11 7-4 7-11 7S1 12 1 12z"/>
										<circle cx="12" cy="12" r="3"/>
									</svg>
									<svg v-else class="h-4 w-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round">
										<path d="M17.94 17.94A10.94 10.94 0 0 1 12 19c-7 0-11-7-11-7a19.79 19.79 0 0 1 5.06-5.94"/>
										<path d="M9.9 4.24A10.94 10.94 0 0 1 12 4c7 0 11 7 11 7a19.79 19.79 0 0 1-3.17 4.19"/>
										<path d="M14.12 14.12a3 3 0 1 1-4.24-4.24"/>
										<path d="M1 1l22 22"/>
									</svg>
								</button>
							</div>
						</div>

						<!-- Remember me + Forgot Password -->
						<div class="flex items-center justify-between pt-0.5">
							<label class="remember-label">
								<input type="checkbox" v-model="rememberMe" class="remember-check"/>
								Remember me
							</label>
							<a :href="`/login#forgot`" class="forgot-link">Forgot Password?</a>
						</div>

						<!-- Sign In button -->
						<button type="submit" class="signin-btn" :disabled="loading">
							<span v-if="!loading">Sign In</span>
							<span v-else class="flex items-center justify-center gap-2">
								<span class="inline-block h-3.5 w-3.5 animate-spin rounded-full border-2 border-white/40 border-t-white"></span>
								Signing in…
							</span>
						</button>

					</form>

					<p class="card-footer-note">
						Protected by Frappe / ERPNext authentication
					</p>
				</div>
			</main>

		</div>
	</div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { call, ensureCsrfReady } from "@/api";

const router = useRouter();

const email        = ref("");
const password     = ref("");
const loading      = ref(false);
const error        = ref("");
const showPassword = ref(false);
const rememberMe   = ref(false);

const brandLogo    = ref("");
const brandName    = ref("");
const brandTagline = ref("");

onMounted(async () => {
	try {
		const b = await call({ method: "portal_app.api.public.get_branding" });
		if (b?.company_logo)    brandLogo.value    = b.company_logo;
		if (b?.company_name)    brandName.value    = b.company_name;
		if (b?.company_tagline) brandTagline.value = b.company_tagline;
	} catch { /* ignore */ }
});

const showToast = (message) => {
	error.value = message;
	setTimeout(() => (error.value = ""), 4500);
};

const handleLogin = async () => {
	if (!email.value.trim() || !password.value) {
		showToast("Please enter email and password.");
		return;
	}
	loading.value = true;
	error.value   = "";
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
		try {
			const msgs = JSON.parse(data._server_messages);
			if (msgs.length) {
				try { return JSON.parse(msgs[0]).message; } catch { return msgs[0]; }
			}
		} catch { /* */ }
	}
	return data?.message || data?.exception || "Something went wrong";
};
</script>

<style scoped>
/* ── Shell & grid ── */
.login-shell {
	min-height: 100vh;
	background: #fdf8f0;
	color: #111827;
	font-family: inherit;
}

.login-grid {
	display: grid;
	min-height: 100vh;
	grid-template-columns: 1fr;
}
@media (min-width: 1024px) {
	.login-grid { grid-template-columns: 1.25fr 1fr; }
}

/* ── Left panel ── */
.left-panel {
	display: none;
	position: relative;
	flex-direction: column;
	overflow: hidden;
	background: #fdf8f0;
	padding: 2.5rem 2.75rem;
}
@media (min-width: 1024px) {
	.left-panel { display: flex; }
}

/* Building art – fills lower 60% */
.buildings-art {
	position: absolute;
	bottom: 80px;
	left: 0;
	right: 0;
	width: 100%;
	height: 62%;
	opacity: 0.38;
	pointer-events: none;
}

/* Wave curves – sit at very bottom */
.waves-art {
	position: absolute;
	bottom: 0;
	left: 0;
	right: 0;
	width: 100%;
	height: 110px;
	pointer-events: none;
}

/* Brand block – top */
.brand-top {
	position: relative;
	z-index: 10;
	display: flex;
	align-items: center;
	gap: 0.85rem;
}
.brand-mark {
	color: #1a1208;
	flex-shrink: 0;
}
.brand-text {
	min-width: 0;
}
.brand-name {
	font-size: 10px;
	font-weight: 700;
	text-transform: uppercase;
	letter-spacing: 0.18em;
	color: #3d2e1a;
	line-height: 1.3;
}
.brand-sub {
	font-size: 9px;
	text-transform: uppercase;
	letter-spacing: 0.14em;
	color: #9c7c56;
	margin-top: 2px;
}

/* Headline – center of panel */
.brand-headline {
	position: relative;
	z-index: 10;
	flex: 1;
	display: flex;
	flex-direction: column;
	justify-content: center;
}
.headline-title {
	font-size: clamp(2.2rem, 3.5vw, 3rem);
	font-weight: 800;
	line-height: 1.04;
	letter-spacing: -0.025em;
	color: #1c1208;
}
.headline-sub {
	margin-top: 0.75rem;
	font-size: 0.95rem;
	color: #7c6040;
	line-height: 1.5;
}

/* Copyright */
.brand-copy {
	position: relative;
	z-index: 10;
	font-size: 10px;
	color: #b09070;
	padding-bottom: 0.25rem;
}

/* ── Right panel ── */
.right-panel {
	background: #fdf8f0;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 1.5rem;
}
@media (min-width: 640px) {
	.right-panel { padding: 3rem; }
}

/* ── Login card ── */
.login-card {
	width: 100%;
	max-width: 420px;
	background: #fffdf8;
	border-radius: 20px;
	padding: 2.25rem 2.25rem 2rem;
	border: 1px solid #ede8df;
	box-shadow:
		0 2px 8px rgba(120,80,20,0.06),
		0 16px 48px -12px rgba(120,80,20,0.14);
}

/* Mobile logo */
.mobile-logo {
	display: flex;
	justify-content: center;
	margin-bottom: 1.5rem;
}
@media (min-width: 1024px) {
	.mobile-logo { display: none; }
}

/* Card header */
.card-header {
	margin-bottom: 1.75rem;
}
.card-title {
	font-size: 1.55rem;
	font-weight: 800;
	color: #1c1208;
	letter-spacing: -0.02em;
	line-height: 1.15;
}
.card-sub {
	margin-top: 0.35rem;
	font-size: 0.86rem;
	color: #7c6040;
	line-height: 1.5;
}

/* ── Field labels ── */
.field-label {
	display: block;
	margin-bottom: 0.45rem;
	font-size: 12px;
	font-weight: 600;
	color: #374151;
	letter-spacing: 0.01em;
}

/* ── Inputs ── */
.field-input {
	width: 100%;
	padding: 0.7rem 0.95rem;
	border-radius: 11px;
	border: 1.5px solid #e8e0d5;
	background: #fdf9f4;
	color: #1c1208;
	font-size: 0.9rem;
	line-height: 1.4;
	transition: border-color 0.15s ease, box-shadow 0.15s ease, background 0.15s ease;
	-webkit-appearance: none;
}
.field-input::placeholder {
	color: #9ca3af;
}
.field-input:focus {
	outline: none;
	background: #fffdf8;
	border-color: var(--portal-accent);
	box-shadow: 0 0 0 3px var(--portal-accent-soft);
}

/* Eye toggle */
.eye-btn {
	position: absolute;
	right: 0.6rem;
	top: 50%;
	transform: translateY(-50%);
	padding: 0.35rem;
	border-radius: 7px;
	color: #9ca3af;
	background: transparent;
	border: none;
	cursor: pointer;
	transition: color 0.15s ease, background 0.15s ease;
}
.eye-btn:hover {
	color: #6b7280;
	background: #f3f4f6;
}

/* ── Remember me ── */
.remember-label {
	display: flex;
	align-items: center;
	gap: 0.5rem;
	font-size: 0.875rem;
	color: #4a3520;
	cursor: pointer;
	user-select: none;
}
.remember-check {
	width: 15px;
	height: 15px;
	border-radius: 4px;
	accent-color: var(--portal-accent);
	cursor: pointer;
	flex-shrink: 0;
}

/* ── Forgot password link ── */
.forgot-link {
	font-size: 0.875rem;
	font-weight: 500;
	color: var(--portal-accent);
	text-decoration: none;
	transition: opacity 0.15s ease;
}
.forgot-link:hover { opacity: 0.72; }

/* ── Sign In button — fixed gold to match brand/reference ── */
.signin-btn {
	width: 100%;
	padding: 0.85rem 1.5rem;
	border-radius: 12px;
	font-size: 0.95rem;
	font-weight: 700;
	letter-spacing: 0.02em;
	color: #ffffff;
	background: linear-gradient(135deg, #c9a024 0%, #a67c10 100%);
	border: 1px solid rgba(166, 124, 16, 0.35);
	cursor: pointer;
	transition: opacity 0.15s ease, transform 0.1s ease, box-shadow 0.2s ease;
	box-shadow: 0 6px 22px -6px rgba(166, 124, 16, 0.55);
	text-shadow: 0 1px 2px rgba(100, 60, 0, 0.25);
}
.signin-btn:hover:not(:disabled) {
	background: linear-gradient(135deg, #b8900e 0%, #96700a 100%);
	transform: translateY(-1px);
	box-shadow: 0 10px 28px -6px rgba(166, 124, 16, 0.65);
}
.signin-btn:active:not(:disabled) {
	transform: translateY(0);
	box-shadow: 0 4px 12px -4px rgba(166, 124, 16, 0.4);
}
.signin-btn:disabled {
	opacity: 0.6;
	cursor: not-allowed;
}

/* ── Card footer note ── */
.card-footer-note {
	margin-top: 1.5rem;
	text-align: center;
	font-size: 11px;
	color: #d1d5db;
}

/* ── Toast transition ── */
.slide-toast-enter-active { transition: all 0.3s cubic-bezier(0.34,1.56,0.64,1); }
.slide-toast-leave-active { transition: all 0.2s ease; }
.slide-toast-enter-from   { opacity: 0; transform: translateY(10px) scale(0.96); }
.slide-toast-leave-to     { opacity: 0; transform: translateY(8px); }
</style>
