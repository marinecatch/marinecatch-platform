// src/pages/WhatsAppInbox.jsx
import { useEffect, useState } from 'react';
import Layout from '../components/Layout';
import { getWhatsappConversations, getWhatsappConversation, getWhatsappOverview } from '../services/api';

function StatCard({ label, value }) {
  return (
    <div style={{ background:'white', borderRadius:8, padding:'16px 18px', border:'1px solid #e2e8f0', flex:1, minWidth:150 }}>
      <div style={{ fontSize:11, color:'#718096', textTransform:'uppercase', fontWeight:600, marginBottom:6 }}>{label}</div>
      <div style={{ fontSize:22, fontWeight:700, color:'#0D2137' }}>{value}</div>
    </div>
  );
}

export default function WhatsAppInbox() {
  const [overview, setOverview]       = useState(null);
  const [conversations, setConversations] = useState([]);
  const [active, setActive]           = useState(null);
  const [messages, setMessages]       = useState([]);
  const [loading, setLoading]         = useState(true);

  useEffect(() => {
    Promise.all([getWhatsappOverview(), getWhatsappConversations()])
      .then(([o, c]) => {
        setOverview(o.data);
        setConversations(c.data.conversations || []);
        if (c.data.conversations?.length) openConversation(c.data.conversations[0].phone_number);
      }).catch(console.error).finally(() => setLoading(false));
  }, []);

  const openConversation = (phone) => {
    setActive(phone);
    getWhatsappConversation(phone).then(r => setMessages(r.data.messages || [])).catch(console.error);
  };

  return (
    <Layout title="WhatsApp Inbox" subtitle="Conversation log across buyers, fishers & leads">
      {loading ? (
        <div style={{ textAlign:'center', padding:40, color:'#718096' }}>Loading conversations...</div>
      ) : (
        <>
          <div style={{ display:'flex', gap:16, flexWrap:'wrap', marginBottom:20 }}>
            <StatCard label="Total Messages" value={overview.total_messages} />
            <StatCard label="Conversations" value={overview.total_conversations} />
            <StatCard label="Inbound" value={overview.inbound} />
            <StatCard label="Outbound" value={overview.outbound} />
          </div>

          <div style={{ display:'flex', gap:0, background:'white', borderRadius:8, border:'1px solid #e2e8f0', overflow:'hidden', height:520 }}>
            <div style={{ width:300, borderRight:'1px solid #e2e8f0', overflowY:'auto' }}>
              {conversations.map(c => (
                <div key={c.phone_number} onClick={() => openConversation(c.phone_number)}
                  style={{
                    padding:'12px 16px', cursor:'pointer', borderBottom:'1px solid #f7fafc',
                    background: active === c.phone_number ? '#ebf8ff' : 'transparent',
                  }}>
                  <div style={{ display:'flex', justifyContent:'space-between' }}>
                    <span style={{ fontWeight:600, fontSize:13 }}>{c.sender_name || c.phone_number}</span>
                    <span style={{ fontSize:10, color:'#a0aec0' }}>{c.user_role}</span>
                  </div>
                  <div style={{ fontSize:12, color:'#718096', whiteSpace:'nowrap', overflow:'hidden', textOverflow:'ellipsis', marginTop:2 }}>
                    {c.direction === 'inbound' ? '← ' : '→ '}{c.last_message}
                  </div>
                </div>
              ))}
              {conversations.length === 0 && <div style={{ padding:16, color:'#a0aec0', fontSize:13 }}>No conversations yet.</div>}
            </div>

            <div style={{ flex:1, display:'flex', flexDirection:'column', padding:16, overflowY:'auto' }}>
              {active ? (
                messages.map((m, i) => (
                  <div key={i} style={{
                    alignSelf: m.direction === 'inbound' ? 'flex-start' : 'flex-end',
                    background: m.direction === 'inbound' ? '#f7fafc' : '#1D60AE',
                    color: m.direction === 'inbound' ? '#1a365d' : 'white',
                    padding:'8px 12px', borderRadius:10, marginBottom:8, maxWidth:'70%', fontSize:13,
                  }}>
                    <div>{m.message_text}</div>
                    <div style={{ fontSize:10, opacity:0.7, marginTop:4 }}>{m.created_at ? new Date(m.created_at).toLocaleString() : ''}</div>
                  </div>
                ))
              ) : (
                <div style={{ color:'#a0aec0', textAlign:'center', marginTop:40 }}>Select a conversation</div>
              )}
            </div>
          </div>
        </>
      )}
    </Layout>
  );
}
