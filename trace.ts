import fetch from 'node-fetch';

async function run() {
  // Try to hit the API server running directly, we'll see if it's there
  try {
    const loginRes = await fetch("http://localhost:3000/api/v1/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: new URLSearchParams({ username: "owner1@test.com", password: "password123" })
    });
    const { access_token } = await loginRes.json();
    const headers = { Authorization: `Bearer ${access_token}` };

    console.log("1. GET /organizations/current");
    const res1 = await fetch("http://localhost:3000/api/v1/organizations/current", { headers });
    console.log(await res1.json());

    console.log("2. PATCH /organizations/current");
    const res2 = await fetch("http://localhost:3000/api/v1/organizations/current", { 
        method: "PATCH", 
        headers: { ...headers, "Content-Type": "application/json" },
        body: JSON.stringify({ workspace_type: "AGENCY" })
    });
    console.log(await res2.json());

    console.log("3. GET /organizations/current");
    const res3 = await fetch("http://localhost:3000/api/v1/organizations/current", { headers });
    console.log(await res3.json());
  } catch(e) {
    console.error(e);
  }
}

run();
