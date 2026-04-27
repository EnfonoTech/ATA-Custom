frappe.pages["portal_app"].on_page_load = function (wrapper) {
    var link = document.createElement("link");
    link.rel = "stylesheet";
    link.href = "/assets/portal_app/frontend/assets/index.css";
    link.onload = function () {
        wrapper.innerHTML = `<div id="app"></div>`;
        var _$ = window.$;
        var _jQuery = window.jQuery;
        var script = document.createElement("script");
        script.src = "/assets/portal_app/frontend/frontend.js";
        script.onload = function () {
            window.$ = _$;
            window.jQuery = _jQuery;
        };
        document.body.appendChild(script);
    };
    document.head.appendChild(link);
};
