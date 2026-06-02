import fetch from 'node-fetch';

async function runTest() {
    try {
        // Assume dev server is running on 3000
        const loginRes = await fetch("http://127.0.0.1:3000/api/v1/auth/login", {
            method: "POST",
            headers: { "Content-Type": "application/x-www-form-urlencoded" },
            body: new URLSearchParams({ username: "sanjith.k.m12@gmail.com", password: "password123" }) // try standard or we can just bypass auth
        });
        
        if (!loginRes.ok) {
            console.log("Login failed", loginRes.status, await loginRes.text());
        }
    } catch (e) {
        console.error("fetch failed", e);
    }
}
runTest();
