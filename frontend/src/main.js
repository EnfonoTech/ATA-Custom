import { createApp } from "vue";
import App from "./App.vue";
import "../style.css";
import "./styles/tooltip.css";
import router from "./router";

document.documentElement.classList.remove("dark");
try {
	const savedTheme = localStorage.getItem("portal_theme") || "indigo";
	if (savedTheme && savedTheme !== "indigo") {
		document.documentElement.setAttribute("data-theme", savedTheme);
	}
} catch {
	/* ignore */
}

createApp(App).use(router).mount("#app");
