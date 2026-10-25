const API = "https://api.github.com";
const OWNER = "Niroop-H";
const REPO = "Verifier";
const WORKFLOW = "aegis-web-simulation.yml";
function headers(token) { return { Authorization: "Bearer " + token, Accept: "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28" }; }
function json(res, status, body) { res.statusCode=status; res.setHeader("Content-Type","application/json; charset=utf-8"); res.setHeader("Cache-Control","no-store"); res.end(JSON.stringify(body)); }
function validModule(s) { return typeof s==="string" && /^[A-Za-z_][A-Za-z0-9_$]{0,100}$/.test(s); }
module.exports = async (req, res) => {
  const token=process.env.GITHUB_TOKEN;
  if (!token) return json(res,503,{error:"Verification runner is not configured. Add GITHUB_TOKEN in Vercel Project Settings → Environment Variables, then redeploy."});
  if (req.method==="POST") {
    let body=req.body;
    if (typeof body==="string") { try { body=JSON.parse(body); } catch { return json(res,400,{error:"Invalid JSON request."}); } }
    body=body||{};
    const rtl=String(body.rtl||""); const testbench=String(body.testbench||"");
    const top=String(body.top_module||""); const tbtop=String(body.testbench_top||"");
    if (!rtl.trim() || !testbench.trim()) return json(res,400,{error:"Provide both RTL source and a testbench."});
    if (Buffer.byteLength(rtl,"utf8")>40000 || Buffer.byteLength(testbench,"utf8")>20000) return json(res,413,{error:"RTL limit is 40 KB and testbench limit is 20 KB."});
    if (!validModule(top)||!validModule(tbtop)) return json(res,400,{error:"Top module names must be valid Verilog identifiers."});
    const jobId=Date.now().toString(36)+"-"+Math.random().toString(36).slice(2,9);
    const payload={ref:"main",inputs:{job_id:jobId,rtl_base64:Buffer.from(rtl,"utf8").toString("base64"),testbench_base64:Buffer.from(testbench,"utf8").toString("base64"),top_module:top,testbench_top:tbtop}};
    const r=await fetch(API+`/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/dispatches`,{method:"POST",headers:{...headers(token),"Content-Type":"application/json"},body:JSON.stringify(payload)});
    if (!r.ok) return json(res,502,{error:"Could not start the isolated verification runner. Check that the Vercel token has Actions write permission and the workflow is enabled.",detail:(await r.text()).slice(0,700)});
    return json(res,202,{job_id:jobId,status:"QUEUED",message:"Job dispatched to an isolated GitHub Actions runner.",status_url:"/api/verify?job_id="+encodeURIComponent(jobId)});
  }
  if (req.method==="GET") {
    const jobId=String(req.query?.job_id||"");
    if (!/^[a-z0-9-]{5,80}$/.test(jobId)) return json(res,400,{error:"Provide a valid job_id."});
    const r=await fetch(API+`/repos/${OWNER}/${REPO}/actions/workflows/${WORKFLOW}/runs?per_page=20`,{headers:headers(token)});
    if (!r.ok) return json(res,502,{error:"Unable to check runner status.",detail:(await r.text()).slice(0,500)});
    const data=await r.json();
    const run=(data.workflow_runs||[]).find(x=>x.display_title==="AEGIS-WEB-"+jobId);
    if (!run) return json(res,200,{job_id:jobId,status:"QUEUED",message:"Waiting for the hosted runner to start."});
    let artifactUrl=null;
    if (run.status==="completed") {
      const ar=await fetch(API+`/repos/${OWNER}/${REPO}/actions/runs/${run.id}/artifacts`,{headers:headers(token)});
      if(ar.ok){const ad=await ar.json();const a=(ad.artifacts||[]).find(x=>x.name==="aegis-result-"+jobId && !x.expired);if(a)artifactUrl=a.archive_download_url;}
    }
    return json(res,200,{job_id:jobId,status:run.status==="completed"?(run.conclusion==="success"?"COMPLETED":"ERROR"):run.status.toUpperCase(),conclusion:run.conclusion,run_url:run.html_url,artifact_url:artifactUrl,message:run.status==="completed"?"Runner finished. Download the result artifact to inspect logs and JSON evidence.":"Verification is running in an isolated worker."});
  }
  res.setHeader("Allow","GET, POST"); return json(res,405,{error:"Method not allowed."});
};