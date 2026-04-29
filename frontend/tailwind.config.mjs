import frappeUiPreset from "frappe-ui/tailwind";

export default {
    darkMode: "media",
    presets: [
        frappeUiPreset
    ],
    content: [
        "./index.html",
        "./src/**/*.{vue,js,ts,jsx,tsx}",
        "./node_modules/frappe-ui/src/**/*.{vue,js,ts}"
    ],
    theme: {
        extend: {},
    },
    plugins: [],
};
