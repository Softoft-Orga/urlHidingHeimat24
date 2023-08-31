const originalFetch = window.fetch;
console.log("LOADED MY SCRIPT !!!")
window.fetch = async (url, options) => {
    console.log("Intercepted:", url, options);

    // Perform the original fetch operation
    url = "/heimat24-chat?url=" + url;
    const response = await originalFetch(url, options);

    return response;
};

const originalOpen = XMLHttpRequest.prototype.open;
XMLHttpRequest.prototype.open = function (method, url, async, user, pass) {
    console.log("Intercepted!  ")
    // Intercept and possibly modify method and url here
    originalOpen.call(this, method, url, async, user, pass);
};


