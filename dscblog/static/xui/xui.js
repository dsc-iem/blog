//determines if the user has a set theme
function detectColorTheme() {
    var theme = "light";
    //local storage is used to override OS theme settings
    if (localStorage.getItem("theme")) {
        if (localStorage.getItem("theme") == "dark") {
            theme = "dark";
        }
    }
    else if (window.matchMedia("(prefers-color-scheme: dark)").matches) {
        theme = "dark";
    }
    //dark theme preferred, set document with a `data-theme` attribute
    if (theme == "dark") {
        document.documentElement.setAttribute("data-theme", "dark");
    }
    else {
        document.documentElement.setAttribute("data-theme", "light");
    }
}

window.detectColorTheme();

matchMedia("(prefers-color-scheme: dark)").addListener(window.detectColorTheme);

window.changeTheme = function (to = 'system') {
    if (to == 'dark') {
        localStorage.setItem('theme', 'dark');
    }
    else if (to == 'light') {
        localStorage.setItem('theme', 'light');
    }
    else {
        localStorage.removeItem('theme');
    }
    window.detectColorTheme();
}