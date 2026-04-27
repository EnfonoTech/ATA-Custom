import { createApp } from "vue";
import App from "./App.vue";
import "../style.css";
import "./styles/tooltip.css";
import router from "./router";

document.documentElement.classList.remove("dark");
try {
	localStorage.removeItem("portal_theme");
} catch {
	/* ignore */
}

createApp(App).use(router).mount("#app");
