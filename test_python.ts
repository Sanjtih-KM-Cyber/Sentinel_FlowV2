import { exec } from "child_process";

exec("python3 backend/run_trace.py", {env: {...process.env, PYTHONPATH: "./backend"}}, (error, stdout, stderr) => {
  console.log("stdout:", stdout);
  console.log("stderr:", stderr);
});
