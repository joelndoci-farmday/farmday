import React,{useState} from 'react';
import {ShieldCheck,X} from 'lucide-react';
import {REGISTRATION_TERMS,REGISTRATION_TERMS_VERSION} from '../lib/registrationTerms';
export default function AgreementModal({onAccept,onDecline,busy=false,allowDecline=true}){
 const [checked,setChecked]=useState(false);
 return <div className="agreement-overlay" role="presentation"><section className="agreement-modal" role="dialog" aria-modal="true" aria-labelledby="agreement-title">
 <div className="agreement-heading"><div className="agreement-icon"><ShieldCheck size={25}/></div><div><h2 id="agreement-title">Welcome to FarmDay</h2><p>Terms of Service · Privacy · Content Publishing License</p></div>{allowDecline&&<button type="button" className="agreement-dismiss" aria-label="Decline and close" onClick={onDecline}><X size={20}/></button>}</div>
 <p className="agreement-intro">Please review and accept the agreement to continue. Your uploads may be published and commercially monetized by FarmDay, including on its official YouTube channel. No automatic revenue share is provided to creators.</p>
 <label className="agreement-choice"><input type="checkbox" checked={checked} onChange={e=>setChecked(e.target.checked)}/><span>I Agree to the Terms of Service, Privacy Policy and Content Publishing License.</span></label>
 <div className="agreement-actions"><button type="button" className="btn primary" disabled={!checked||busy} onClick={onAccept}>{busy?'Saving agreement…':'I Agree & Continue'}</button>{allowDecline&&<button type="button" className="btn outline" disabled={busy} onClick={onDecline}>Decline</button>}</div>
 <div className="agreement-scroll" tabIndex="0" aria-label="Full agreement terms"><strong>FarmDay · Terms of Service</strong><p>Version {REGISTRATION_TERMS_VERSION} · Read these provisions before accepting. This text describes our current agreement; a separate detailed privacy notice should be published before launch.</p>{REGISTRATION_TERMS.map(([heading,body],i)=><section key={heading}><strong>{i+1}. {heading}</strong><p>{body}</p></section>)}</div>
 </section></div>
}
