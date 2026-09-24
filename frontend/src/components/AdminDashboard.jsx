import React, { useState, useEffect } from 'react';
import { X, Play, Trash2, Settings, RefreshCw } from 'lucide-react';

const BACKEND_URL = "http://localhost:8001";

const AdminDashboard = ({ onClose }) => {
  const [config, setConfig] = useState({ seed_urls: [], max_depth: 1, download_limit: 5 });
  const [documents, setDocuments] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isSpiderRunning, setIsSpiderRunning] = useState(false);
  const [newUrl, setNewUrl] = useState('');

  useEffect(() => {
    fetchConfig();
    fetchDocuments();
  }, []);

  const fetchConfig = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/admin/config`);
      const data = await res.json();
      setConfig(data);
    } catch (e) {
      console.error(e);
    }
  };

  const fetchDocuments = async () => {
    try {
      const res = await fetch(`${BACKEND_URL}/api/admin/documents`);
      const data = await res.json();
      setDocuments(data);
    } catch (e) {
      console.error(e);
    }
  };

  const runSpider = async () => {
    setIsSpiderRunning(true);
    try {
      const res = await fetch(`${BACKEND_URL}/api/pipeline/run`, { method: 'POST' });
      await res.json();
      fetchDocuments(); // Refresh docs after running
    } catch (e) {
      alert("Spider failed to run");
    }
    setIsSpiderRunning(false);
  };

  const saveConfig = async (newConfig) => {
    setConfig(newConfig);
    try {
      await fetch(`${BACKEND_URL}/api/admin/config`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newConfig)
      });
    } catch (e) {
      console.error(e);
    }
  };

  const addUrl = () => {
    if (!newUrl) return;
    saveConfig({ ...config, seed_urls: [...config.seed_urls, newUrl] });
    setNewUrl('');
  };

  const removeUrl = (urlToRemove) => {
    saveConfig({ ...config, seed_urls: config.seed_urls.filter(u => u !== urlToRemove) });
  };

  const deleteDocument = async (filename) => {
    if (!window.confirm(`Are you sure you want to permanently delete ${filename} from the AI's memory?`)) return;
    
    try {
      await fetch(`${BACKEND_URL}/api/admin/documents/${filename}`, { method: 'DELETE' });
      fetchDocuments();
    } catch (e) {
      console.error(e);
    }
  };

  return (
    <div className="modal-overlay" onClick={onClose} style={{ zIndex: 1000 }}>
      <div className="modal-content" style={{ width: '80%', maxWidth: '800px', maxHeight: '90vh', overflowY: 'auto' }} onClick={e => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Admin Control Center</h2>
          <button className="close-btn" onClick={onClose}><X size={24}/></button>
        </div>
        
        <div style={{ display: 'grid', gap: '20px', gridTemplateColumns: '1fr 1fr' }}>
          
          {/* SPIDER CONTROL */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <h3><Play size={18} style={{ display: 'inline', marginRight: '8px' }}/> Autonomous Spider</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '14px' }}>Manually trigger the data ingestion pipeline.</p>
            <button 
              className="btn-primary" 
              onClick={runSpider} 
              disabled={isSpiderRunning}
              style={{ padding: '15px', fontSize: '16px', display: 'flex', justifyContent: 'center', alignItems: 'center', gap: '10px' }}
            >
              {isSpiderRunning ? <RefreshCw className="spin" size={20} /> : <Play size={20} />}
              {isSpiderRunning ? 'Scraping & Embedding...' : 'Run Spider Now'}
            </button>
          </div>

          {/* SETTINGS */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '15px' }}>
            <h3><Settings size={18} style={{ display: 'inline', marginRight: '8px' }}/> Crawler Configuration</h3>
            
            <div style={{ display: 'flex', gap: '10px' }}>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Max Depth</label>
                <input 
                  type="number" 
                  className="input-field" 
                  value={config.max_depth} 
                  onChange={e => saveConfig({...config, max_depth: parseInt(e.target.value)})}
                  min="0" max="3"
                />
              </div>
              <div style={{ flex: 1 }}>
                <label style={{ fontSize: '12px', color: 'var(--text-muted)' }}>PDF Limit</label>
                <input 
                  type="number" 
                  className="input-field" 
                  value={config.download_limit} 
                  onChange={e => saveConfig({...config, download_limit: parseInt(e.target.value)})}
                  min="1" max="50"
                />
              </div>
            </div>

            <div>
              <label style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Target URLs</label>
              <div style={{ display: 'flex', gap: '5px', marginBottom: '10px' }}>
                <input 
                  className="input-field" 
                  placeholder="https://example.gov.in" 
                  value={newUrl} 
                  onChange={e => setNewUrl(e.target.value)}
                />
                <button className="btn-primary" onClick={addUrl}>Add</button>
              </div>
              <div style={{ maxHeight: '100px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '5px' }}>
                {config.seed_urls.map(url => (
                  <div key={url} style={{ display: 'flex', justifyContent: 'space-between', background: 'var(--glass-bg)', padding: '5px 10px', borderRadius: '4px', fontSize: '14px' }}>
                    <span style={{ overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{url}</span>
                    <button onClick={() => removeUrl(url)} style={{ background: 'none', border: 'none', color: '#ff4444', cursor: 'pointer' }}><Trash2 size={16} /></button>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* KNOWLEDGE BASE INVENTORY */}
          <div className="glass-panel" style={{ gridColumn: '1 / -1', padding: '20px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '15px' }}>
              <h3>Knowledge Base Inventory ({documents.length} docs)</h3>
              <button className="btn-outline" onClick={fetchDocuments} style={{ padding: '5px 10px', fontSize: '12px' }}>
                <RefreshCw size={14} style={{ marginRight: '5px', verticalAlign: 'middle' }}/> Refresh
              </button>
            </div>
            
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', textAlign: 'left', borderCollapse: 'collapse', fontSize: '14px' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid var(--border-color)', color: 'var(--text-muted)' }}>
                    <th style={{ padding: '10px' }}>Document Name</th>
                    <th style={{ padding: '10px' }}>Date Ingested</th>
                    <th style={{ padding: '10px' }}>Size (KB)</th>
                    <th style={{ padding: '10px' }}>Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {documents.length === 0 ? (
                    <tr><td colSpan="4" style={{ textAlign: 'center', padding: '20px', color: 'var(--text-muted)' }}>No documents in memory.</td></tr>
                  ) : (
                    documents.map(doc => (
                      <tr key={doc.archive_name} style={{ borderBottom: '1px solid var(--border-color)' }}>
                        <td style={{ padding: '10px', maxWidth: '300px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }} title={doc.original_name}>{doc.original_name}</td>
                        <td style={{ padding: '10px' }}>{doc.date_ingested}</td>
                        <td style={{ padding: '10px' }}>{doc.size_kb}</td>
                        <td style={{ padding: '10px' }}>
                          <button 
                            onClick={() => deleteDocument(doc.archive_name)}
                            style={{ background: 'none', border: 'none', color: '#ff4444', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '5px' }}
                            title="Purge from Vector DB"
                          >
                            <Trash2 size={16}/> Purge
                          </button>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default AdminDashboard;
