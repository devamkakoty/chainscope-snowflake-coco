"use strict";
// Static, public synthetic evidence replay. This is NOT an authorization boundary.
(() => {
  let role="operations", sequence=0, tail="0".repeat(64);
  const audit=[];
  const copy=(value)=>JSON.parse(JSON.stringify(value));
  const normalize=(s)=>s.toLowerCase().replace(/[^a-z0-9]+/g," ").trim();
  const data=window.CHAINSCOPE_DATA;
  async function hash(value){
    const bytes=new TextEncoder().encode(JSON.stringify(value));
    return [...new Uint8Array(await crypto.subtle.digest("SHA-256",bytes))].map(b=>b.toString(16).padStart(2,"0")).join("");
  }
  async function log(metric,decision,response){
    const entry={sequence:++sequence,at:new Date().toISOString(),metric_id:metric,role,decision,
      result_sha256:await hash(response),previous_sha256:tail};
    entry.sha256=await hash(entry);tail=entry.sha256;audit.push(entry);
    if(audit.length>100)audit.shift();
    return sequence;
  }
  const fail=(status,error,message)=>Object.assign(new Error(message),{status,data:{status:"refused",error,message}});
  window.CHAINSCOPE_REPLAY={api:async(path,body)=>{
    if(path==="/api/session"&&body){role=body.role;return {role,simulated_identity:true};}
    if(path==="/api/session")return {role,roles:data.roles,simulated_identity:true};
    if(path==="/api/overview")return copy(data.overviews[role]);
    if(path==="/api/catalog")return {metrics:copy(data.overviews[role].catalog)};
    if(path==="/api/ontology")return copy(data.ontology);
    if(path==="/api/audit")return {entries:copy(audit),durability:"Public static replay; illustrative only"};
    if(path.startsWith("/api/records/")){
      const value=data.records[role][path];
      if(!value)throw fail(404,"not_found","Source record not found.");
      return copy(value);
    }
    if(path==="/api/ask"){
      const key=typeof body.question==="string"?normalize(body.question):"";
      const metric=data.aliases[key];
      if(!metric){
        const error=fail(422,"unsupported_question","That question is outside the approved metric catalog. No SQL or speculative answer was generated.");
        await log("outside_catalog","refused",error.data);throw error;
      }
      if(metric==="revenue_at_risk"&&role!=="commercial"){
        const error=fail(403,"forbidden_metric","Revenue exposure requires the Commercial analyst demo role. Static replay only: all fixtures are public.");
        await log(metric,"denied",error.data);throw error;
      }
      const result=copy(data.answers[metric]);
      result.policy.role=role;result.policy.role_label=data.roles[role];
      result.policy.classification=role==="commercial"?"Synthetic commercial":"Synthetic operations";
      result.policy.method="Static replay of precomputed deterministic local results";
      result.audit_sequence=await log(metric,"allowed",result);return result;
    }
    throw fail(404,"not_found","Static replay route unavailable.");
  }};
})();
