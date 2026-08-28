import React, { useState, useEffect, useRef } from 'react';
import { Shield, Moon, Sun, AlertTriangle, CheckCircle, Video, Play, FileText, Activity, Globe, Mic, User, ArrowLeft, Network, Settings, Trash2, Plus, Save } from 'lucide-react';
import { useTranslation } from 'react-i18next';
import { getProfiles, updateProfile, getLogs, addToQueue, startQueue, stopQueue, getQueueStatus, clearLogs, analyzeProfile, moderateAudio, getGraph, getWatchlist, addWatchlist, deleteWatchlist } from './api';
import { Radar, RadarChart, PolarGrid, PolarAngleAxis, PolarRadiusAxis, ResponsiveContainer } from 'recharts';
import ForceGraph2D from 'react-force-graph-2d';

const MOCK_FEED_INITIAL = [];

const SVG_YOUTUBE = <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23.498 6.186a3.016 3.016 0 0 0-2.122-2.136C19.505 3.545 12 3.545 12 3.545s-7.505 0-9.377.505A3.017 3.017 0 0 0 .502 6.186C0 8.07 0 12 0 12s0 3.93.502 5.814a3.016 3.016 0 0 0 2.122 2.136c1.871.505 9.376.505 9.376.505s7.505 0 9.377-.505a3.015 3.015 0 0 0 2.122-2.136C24 15.93 24 12 24 12s0-3.93-.502-5.814zM9.545 15.568V8.432L15.818 12l-6.273 3.568z"/></svg>;
const SVG_TIKTOK = <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M19.59 6.69a4.83 4.83 0 0 1-3.77-4.25V2h-3.45v13.67a2.89 2.89 0 0 1-5.2 1.74 2.89 2.89 0 0 1 2.31-4.64 2.93 2.93 0 0 1 .88.13V9.4a6.84 6.84 0 0 0-1-.05A6.33 6.33 0 0 0 5 20.1a6.34 6.34 0 0 0 10.86-4.43v-7a8.16 8.16 0 0 0 4.77 1.52v-3.4a4.85 4.85 0 0 1-1-.1z"/></svg>;
const SVG_TELEGRAM = <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M11.944 0A12 12 0 0 0 0 12a12 12 0 0 0 12 12 12 12 0 0 0 12-12A12 12 0 0 0 12 0a12 12 0 0 0-.056 0zm4.962 7.224c.1-.002.321.023.465.14a.506.506 0 0 1 .171.325c.016.093.036.306.02.472-.18 1.898-.962 6.502-1.36 8.627-.168.9-.499 1.201-.82 1.23-.696.065-1.225-.46-1.896-.902-1.056-.693-1.653-1.124-2.678-1.8-1.185-.78-.417-1.21.258-1.91.177-.184 3.247-2.977 3.307-3.23.007-.032.014-.15-.056-.212s-.174-.041-.249-.024c-.106.024-1.793 1.14-5.061 3.345-.48.33-.913.49-1.302.48-.428-.008-1.252-.241-1.865-.44-.752-.245-1.349-.374-1.297-.789.027-.216.325-.437.892-.663 3.498-1.524 5.83-2.529 6.998-3.014 3.332-1.386 4.025-1.627 4.476-1.635z"/></svg>;
const SVG_VK = <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M23.117 7.766c.216-.713 0-1.266-1.017-1.266h-2.915c-.833 0-1.233.433-1.433.916 0 0-1.483 3.65-3.583 6.017-.683.683-.983.9-1.4.9-.217 0-.533-.217-.533-.917V7.766c0-.833-.25-1.216-.95-1.216h-5.2c-.516 0-.833.383-.833.733 0 .766 1.133.95 1.25 3.117V14.5c0 1.05-.183 1.233-.6 1.233-1.133 0-3.9-3.683-5.55-7.883-.316-.9-1.033-1.35-1.883-1.35H.416C-.534 6.5-.7 6.966-.7 7.45c0 .883 1.134 5.25 5.3 11.083C7.384 22.5 11.233 24 14.733 24c2.1 0 2.367-.466 2.367-1.266v-2.9c0-.95.2-.134 1.117.8.85.85 2.5 2.5 4.533 2.5h2.917c.95 0 1.417-.484 1.15-1.417-.3-1.066-1.433-2.45-2.933-4.133-1.083-1.233-2.733-2.583-3.216-3.266-.667-.85-.484-1.2 0-1.983 0 0 5.666-8.017 5.866-8.567z"/></svg>;

const INITIAL_RESULTS = {};
const BUILTIN_PROFILE_NAMES = new Set(['strict', 'standard', 'soft']);

function App() {
  const { t, i18n } = useTranslation();
  const [profiles, setProfiles] = useState([]);
  const [activeProfileId, setActiveProfileId] = useState(null);
  
  const [currentView, setCurrentView] = useState('feed'); // 'feed', 'profile', 'graph', 'settings'
  
  const [feedItems, setFeedItems] = useState(MOCK_FEED_INITIAL);
  const [feedResults, setFeedResults] = useState(INITIAL_RESULTS);
  const [isLoading, setIsLoading] = useState(true);
  
  const [urlInput, setUrlInput] = useState("");
  const [isSimulating, setIsSimulating] = useState(false);
  const [isAutoPilot, setIsAutoPilot] = useState(false);
  const [queueSize, setQueueSize] = useState(0);
  const [platformFilter, setPlatformFilter] = useState('all');

  const [focusMode, setFocusMode] = useState(false);
  const [focusTarget, setFocusTarget] = useState(null);
  const [focusResultId, setFocusResultId] = useState(null);
  const [focusTimedOut, setFocusTimedOut] = useState(false);
  const focusTimerRef = useRef(null);
  const focusModeRef = useRef(false);
  const focusTargetRef = useRef(null);
  const focusResultIdRef = useRef(null);

  const [watchlist, setWatchlist] = useState([]);
  const [watchPlatform, setWatchPlatform] = useState('youtube');
  const [watchTarget, setWatchTarget] = useState('');
  const [profileDraft, setProfileDraft] = useState(null);
  const [isSettingsSaving, setIsSettingsSaving] = useState(false);
  
  // Profile Analysis State
  const [profileData, setProfileData] = useState(null);
  const [isProfileLoading, setIsProfileLoading] = useState(false);
  
  // Graph State
  const [graphData, setGraphData] = useState({ nodes: [], edges: [] });
  const [isGraphLoading, setIsGraphLoading] = useState(false);
  const graphContainerRef = useRef(null);
  const [graphDimensions, setGraphDimensions] = useState({ width: 800, height: 600 });
  
  const audioInputRef = useRef(null);
  const [isAudioUploading, setIsAudioUploading] = useState(false);

  const normalizeUrl = (raw) => {
    try {
      let s = raw.trim();
      if (!/^https?:\/\//i.test(s)) s = 'https://' + s;
      const u = new URL(s);
      const host = u.hostname.replace(/^www\./, '').toLowerCase();
      if (['youtube.com', 'm.youtube.com', 'youtube-nocookie.com'].includes(host) && u.pathname === '/watch') {
        const videoId = u.searchParams.get('v');
        if (videoId) return `youtube:${videoId}`;
      }
      if (host === 'youtu.be') {
        const videoId = u.pathname.split('/').filter(Boolean)[0];
        if (videoId) return `youtube:${videoId}`;
      }
      if (host === 'youtube.com' && (u.pathname.startsWith('/shorts/') || u.pathname.startsWith('/embed/'))) {
        const videoId = u.pathname.split('/').filter(Boolean)[1];
        if (videoId) return `youtube:${videoId}`;
      }
      return `${u.protocol}//${host}${(u.pathname || '/').replace(/\/+$/, '').toLowerCase()}`;
    } catch { return raw.trim().replace(/\/+$/, '').toLowerCase(); }
  };

  useEffect(() => {
    focusModeRef.current = focusMode;
    focusTargetRef.current = focusTarget;
    focusResultIdRef.current = focusResultId;
  }, [focusMode, focusTarget, focusResultId]);

  const [isDarkTheme, setIsDarkTheme] = useState(() => {
    const saved = localStorage.getItem('theme');
    return saved !== null ? saved === 'dark' : true;
  });

  useEffect(() => {
    localStorage.setItem('theme', isDarkTheme ? 'dark' : 'light');
    document.documentElement.setAttribute('data-theme', isDarkTheme ? 'dark' : 'light');
  }, [isDarkTheme]);

  useEffect(() => {
    fetchProfiles();
    checkQueueStatus();
  }, []);
  
  useEffect(() => {
    if (currentView === 'graph') {
      const updateDimensions = () => {
        if (graphContainerRef.current) {
          setGraphDimensions({
            width: graphContainerRef.current.offsetWidth,
            height: window.innerHeight - 200
          });
        }
      };
      updateDimensions();
      window.addEventListener('resize', updateDimensions);
      return () => window.removeEventListener('resize', updateDimensions);
    }
  }, [currentView]);

  const fetchProfiles = async () => {
    try {
      const res = await getProfiles();
      setProfiles(res.data);
      if (res.data.length > 0) {
        setActiveProfileId(res.data[0].id);
        setProfileDraft(JSON.parse(JSON.stringify(res.data[0])));
      }
    } catch (error) {
      console.error('Error fetching profiles', error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    const selected = profiles.find(p => p.id === activeProfileId);
    setProfileDraft(selected ? JSON.parse(JSON.stringify(selected)) : null);
  }, [activeProfileId, profiles]);

  const fetchWatchlist = async () => {
    try {
      const res = await getWatchlist();
      setWatchlist(res.data);
    } catch (error) {
      console.error('Error fetching watchlist', error);
    }
  };

  useEffect(() => {
    if (currentView === 'settings') {
      fetchWatchlist();
    }
  }, [currentView]);

  const checkQueueStatus = async () => {
    try {
      const res = await getQueueStatus();
      setIsAutoPilot(res.data.is_autopilot_running);
      setQueueSize(res.data.queue_size);
    } catch (error) {
      console.error('Failed to get queue status', error);
    }
  };

  const toggleAutoPilot = async () => {
    try {
      if (isAutoPilot) {
        await stopQueue();
        setIsAutoPilot(false);
      } else {
        await startQueue(activeProfileId);
        setIsAutoPilot(true);
      }
    } catch (error) {
      console.error('Error toggling queue', error);
    }
  };

  const seenLogsRef = useRef(new Set());
  
  useEffect(() => {
    const interval = setInterval(() => {
      if (currentView === 'feed') {
        fetchLogs();
      }
      checkQueueStatus();
    }, 2500);
    return () => clearInterval(interval);
  }, [currentView]);

  const fetchLogs = async () => {
    try {
      const res = await getLogs();
      const logs = res.data;
      if (!logs || logs.length === 0) return;

      const newFeed = [];
      const resultsToMerge = {};
      
      logs.forEach(log => {
        const id = `log_${log.id}`;
        if (!seenLogsRef.current.has(id)) {
          seenLogsRef.current.add(id);
          
          const transcriptionObj = log.explanation.find(e => e.transcription !== undefined);
          const transcriptionText = log.transcription_text || (transcriptionObj ? transcriptionObj.transcription : "");
          const cleanExplanation = log.explanation.filter(e => e.transcription === undefined);

          const rawPreview = log.content_preview || "";
          const previewParts = rawPreview.split(' ||| ');
          const previewText = previewParts[0];
          const previewUrl = previewParts.length > 1 ? previewParts[1] : previewParts[0];

          newFeed.push({
            id: id,
            type: log.content_type,
            url: previewUrl,
            preview: previewText,
            simulated: false,
            platform: log.source_platform,
            author_handle: log.author_handle,
            author_url: log.author_url,
          });

          resultsToMerge[id] = {
            decision: log.decision,
            scores: log.scores,
            explanation: cleanExplanation,
            transcription: transcriptionText,
            risk_score: log.risk_score
          };
        }
      });

      if (newFeed.length > 0) {
        setFeedItems(prev => [...newFeed, ...prev]);
        setFeedResults(prev => ({ ...prev, ...resultsToMerge }));

        if (focusModeRef.current && !focusResultIdRef.current) {
          const match = newFeed.find(it => normalizeUrl(it.url || '') === focusTargetRef.current);
          if (match) {
            setFocusResultId(match.id);
            setFocusTimedOut(false);
            if (focusTimerRef.current) clearTimeout(focusTimerRef.current);
          }
        }
      }
    } catch (error) {
      console.error("Error fetching logs", error);
    }
  };

  const changeLanguage = (lng) => {
    i18n.changeLanguage(lng).then(() => {
      setFeedResults({...feedResults});
    });
  };

  const handleAnalyzeUrl = async () => {
    if (!urlInput) return;
    const normalized = normalizeUrl(urlInput);

    const existing = feedItems.find(it => normalizeUrl(it.url || '') === normalized);
    if (existing) {
      setFocusMode(true);
      setFocusTarget(normalized);
      setFocusResultId(existing.id);
      setFocusTimedOut(false);
      setUrlInput("");
      return;
    }

    setFocusMode(true);
    setFocusTarget(normalized);
    setFocusResultId(null);
    setFocusTimedOut(false);

    if (focusTimerRef.current) clearTimeout(focusTimerRef.current);
    focusTimerRef.current = setTimeout(() => {
      setFocusTimedOut(true);
    }, 60000);

    setIsSimulating(true);
    try {
      await addToQueue(urlInput, parseInt(activeProfileId, 10));
      setUrlInput("");
      checkQueueStatus();
    } catch (error) {
      console.error('Error adding to queue', error);
      setFocusMode(false);
      setFocusTarget(null);
      alert('Failed to add to queue');
    } finally {
      setIsSimulating(false);
    }
  };
  
  const handleAudioUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setIsAudioUploading(true);
    try {
      await moderateAudio(activeProfileId, file);
      // Wait for next log poll to pick it up
    } catch (error) {
      console.error("Error uploading audio", error);
      alert("Failed to analyze audio");
    } finally {
      setIsAudioUploading(false);
      if (audioInputRef.current) audioInputRef.current.value = "";
    }
  };

  const handleLoadProfile = async (platform, target) => {
    setIsProfileLoading(true);
    setCurrentView('profile');
    try {
      const res = await analyzeProfile({
        platform, target, profile_id: activeProfileId
      });
      setProfileData(res.data);
    } catch (error) {
      console.error("Error analyzing profile", error);
      alert("Failed to analyze profile");
      setCurrentView('feed');
    } finally {
      setIsProfileLoading(false);
    }
  };
  
  const handleLoadGraph = async () => {
    setIsGraphLoading(true);
    setCurrentView('graph');
    try {
      const res = await getGraph(1); // min_degree = 1 to hide isolated nodes
      setGraphData(res.data);
    } catch (error) {
      console.error("Error loading graph", error);
      alert("Failed to load graph");
      setCurrentView('feed');
    } finally {
      setIsGraphLoading(false);
    }
  };

  const exitFocusMode = () => {
    setFocusMode(false);
    setFocusTarget(null);
    setFocusResultId(null);
    setFocusTimedOut(false);
    if (focusTimerRef.current) clearTimeout(focusTimerRef.current);
  };

  const handleClearHistory = async () => {
    if (window.confirm(t('clear_history_confirm'))) {
      try {
        await clearLogs();
        setFeedItems([]);
        setFeedResults({});
        seenLogsRef.current.clear();
      } catch (err) {
        console.error("Failed to clear logs", err);
      }
    }
  };

  const handleAddWatchTarget = async () => {
    if (!watchTarget.trim()) return;
    try {
      await addWatchlist({ platform: watchPlatform, target: watchTarget.trim() });
      setWatchTarget('');
      fetchWatchlist();
    } catch (error) {
      console.error('Failed to add watch target', error);
      alert('Failed to add watch target');
    }
  };

  const handleDeleteWatchTarget = async (id) => {
    try {
      await deleteWatchlist(id);
      fetchWatchlist();
    } catch (error) {
      console.error('Failed to delete watch target', error);
      alert('Failed to delete watch target');
    }
  };

  const handleThresholdChange = (key, value) => {
    setProfileDraft(prev => ({
      ...prev,
      thresholds: {
        ...prev.thresholds,
        [key]: Number(value)
      }
    }));
  };

  const handleSaveProfile = async () => {
    if (!profileDraft) return;
    const selected = profiles.find(p => p.id === profileDraft.id);
    setIsSettingsSaving(true);
    try {
      const res = await updateProfile(profileDraft.id, {
        name: selected && BUILTIN_PROFILE_NAMES.has(selected.name) ? selected.name : profileDraft.name,
        thresholds: profileDraft.thresholds
      });
      setProfiles(prev => prev.map(p => p.id === res.data.id ? res.data : p));
    } catch (error) {
      console.error('Failed to save profile', error);
      alert('Failed to save profile');
    } finally {
      setIsSettingsSaving(false);
    }
  };

  const getProfileTranslation = (name) => {
    const key = `profile_${name.toLowerCase()}`;
    return t(key) === key ? name.toUpperCase() : t(key).toUpperCase();
  };

  const getCategoryTranslation = (cat) => {
    return t(cat) === cat ? cat : t(cat);
  };

  const getStatusTranslation = (status) => {
    const normalized = { allow: 'allowed', block: 'blocked', flag: 'flagged' }[status] || status;
    const key = `status_${normalized.toLowerCase()}`;
    return t(key) === key ? status : t(key);
  };

  if (isLoading) {
    return <div className="app-container"><div className="loader"></div></div>;
  }
  
  const renderCard = (item, res, showProfileBtn = true) => {
    const isBlocked = res?.decision === 'block';
    const isFlagged = res?.decision === 'flag';
    let riskColor = 'var(--allow-color)';
    if (isBlocked) riskColor = 'var(--block-color)';
    else if (isFlagged) riskColor = 'var(--flag-color)';
    
    const riskPercentage = res?.risk_score !== undefined ? Math.round(res.risk_score * 100) : 0;
    
    // Format data for Radar Chart
    const radarData = res?.scores ? Object.entries(res.scores).map(([k, v]) => ({
      subject: getCategoryTranslation(k),
      A: v * 100,
      fullMark: 100,
    })) : [];

    return (
      <div key={item.id || item.post?.post_url} className="feed-card" style={{
        background: 'var(--panel-bg)',
        border: `1px solid ${isBlocked ? 'var(--block-color)' : 'var(--border-color)'}`,
        borderRadius: '16px',
        padding: '1.5rem',
        position: 'relative',
        boxShadow: isBlocked ? '0 0 15px rgba(239, 68, 68, 0.15)' : 'none'
      }}>
        {res && (
          <div style={{
            position: 'absolute',
            top: '12px',
            right: '12px',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'flex-end',
            gap: '8px'
          }}>
            <div className={`status-badge ${isBlocked ? 'blocked' : 'allowed'}`} style={{
              background: isBlocked ? 'var(--block-bg)' : (isFlagged ? '#fff3cd' : 'var(--allow-bg)'),
              color: riskColor,
              padding: '6px 12px',
              borderRadius: '20px',
              fontSize: '0.8rem',
              fontWeight: 'bold',
              display: 'flex',
              alignItems: 'center',
              gap: '4px',
              border: `1px solid ${riskColor}`
            }}>
              {isBlocked ? <AlertTriangle size={14} /> : <CheckCircle size={14} />}
              {getStatusTranslation(res.decision)}
            </div>
            
            <div style={{
              fontSize: '1.2rem',
              fontWeight: 'bold',
              color: riskColor,
              background: 'var(--bg-color)',
              padding: '4px 10px',
              borderRadius: '8px',
              border: '1px solid var(--border-color)'
            }}>
              {t('risk_score')}: {riskPercentage}%
            </div>
          </div>
        )}
        
        <div className="feed-content" style={{ marginTop: '1.5rem', paddingRight: '120px' }}>
          {(item.type === 'video_url' || item.type === 'text' || item.post) && (
            <div style={{ padding: '1rem', background: 'var(--bg-color)', borderRadius: '8px', marginBottom: '1rem' }}>
              <a href={item.url || item.post?.post_url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)', textDecoration: 'none', fontWeight: '500', display: 'flex', alignItems: 'flex-start', gap: '0.75rem', wordBreak: 'break-word' }}>
                <div style={{ flexShrink: 0, display: 'flex', alignItems: 'center', marginTop: '2px' }}>
                  {(item.url || item.post?.post_url)?.includes('youtube') ? SVG_YOUTUBE : 
                   (item.url || item.post?.post_url)?.includes('tiktok') ? SVG_TIKTOK :
                   (item.url || item.post?.post_url)?.includes('vk.com') ? SVG_VK :
                   (item.platform === 'telegram') ? SVG_TELEGRAM :
                   <Play size={16} />}
                </div>
                <span style={{ flex: 1 }}>{item.preview || item.post?.caption_text || item.url || item.post?.post_url}</span>
              </a>
            </div>
          )}
          
          {item.type === 'audio' && (
            <div style={{ padding: '1rem', background: 'var(--bg-color)', borderRadius: '8px', marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.5rem', color: 'var(--accent)', fontWeight: '500' }}>
              <Mic size={18} /> {item.preview}
            </div>
          )}
          
          {res?.transcription && (
            <div style={{ marginTop: '1rem', fontSize: '0.9rem', color: 'var(--text-color)', opacity: 0.8, background: 'var(--bg-color)', padding: '0.75rem', borderRadius: '6px', borderLeft: '3px solid var(--accent)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.5rem', fontWeight: 'bold' }}>
                <FileText size={14} /> {t('transcription')}
              </div>
              "{res.transcription}"
            </div>
          )}
          
          {showProfileBtn && item.author_handle && (
            <button 
              onClick={() => handleLoadProfile(item.platform, item.author_handle)}
              style={{
                marginTop: '1rem',
                padding: '0.5rem 1rem',
                background: 'transparent',
                border: '1px solid var(--accent)',
                color: 'var(--accent)',
                borderRadius: '6px',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                fontWeight: 'bold',
                fontSize: '0.85rem',
                transition: 'all 0.2s'
              }}
              onMouseOver={e => { e.target.style.background = 'var(--accent)'; e.target.style.color = '#fff'; }}
              onMouseOut={e => { e.target.style.background = 'transparent'; e.target.style.color = 'var(--accent)'; }}
            >
              <User size={16} />
              {t('analyze_profile')} ({item.author_handle})
            </button>
          )}
        </div>

        {res?.scores && (
          <div style={{ display: 'flex', marginTop: '1.5rem', borderTop: '1px solid var(--border-color)', paddingTop: '1rem', gap: '2rem' }}>
            {/* Scores List */}
            <div className="scores" style={{ flex: 1 }}>
              {Object.entries(res.scores).map(([cat, score]) => (
                <div key={cat} className="score-row" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem', fontSize: '0.9rem' }}>
                  <span className="score-label" style={{ fontWeight: 500 }}>{getCategoryTranslation(cat)}</span>
                  <div style={{ display: 'flex', alignItems: 'center', flex: 1, marginLeft: '1rem' }}>
                    <div className="score-bar" style={{ flex: 1, height: '8px', background: 'var(--border-color)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div 
                        className="score-fill" 
                        style={{ 
                          width: `${score * 100}%`, height: '100%',
                          background: score > 0.5 ? 'var(--block-color)' : 'var(--accent)',
                          transition: 'width 0.5s ease'
                        }}
                      />
                    </div>
                    <span style={{ marginLeft: '10px', width: '40px', textAlign: 'right', fontWeight: 'bold' }}>
                      {Math.round(score * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Radar Chart */}
            <div style={{ width: '250px', height: '200px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={radarData}>
                  <PolarGrid stroke="var(--border-color)" />
                  <PolarAngleAxis dataKey="subject" tick={{ fill: 'var(--text-secondary)', fontSize: 10 }} />
                  <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                  <Radar name="Score" dataKey="A" stroke={riskColor} fill={riskColor} fillOpacity={0.5} />
                </RadarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="app-container">
      <header className="header">
        <h1><Shield color="var(--accent)" size={32} /> {t('app_title')}</h1>
        <div className="header-controls">
          {currentView !== 'graph' && (
            <button 
              className="action-button"
              onClick={handleLoadGraph}
              style={{ background: 'transparent', border: '1px solid var(--accent)', padding: '0.6rem 1.2rem', borderRadius: '8px', color: 'var(--accent)', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}
            >
              <Network size={18} /> {t('graph_view')}
            </button>
          )}

          {currentView !== 'settings' && (
            <button
              className="action-button"
              onClick={() => setCurrentView('settings')}
              title={t('settings')}
              style={{ background: 'transparent', border: '1px solid var(--accent)', padding: '0.6rem 1rem', borderRadius: '8px', color: 'var(--accent)', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer' }}
            >
              <Settings size={18} /> {t('settings')}
            </button>
          )}

          <button 
            className={`action-button ${isAutoPilot ? 'active-glow' : ''}`}
            onClick={toggleAutoPilot}
            style={{ 
              background: isAutoPilot ? 'var(--danger)' : 'var(--accent)',
              border: 'none', padding: '0.6rem 1.2rem', borderRadius: '8px',
              color: 'white', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: '0.5rem', cursor: 'pointer',
              boxShadow: isAutoPilot ? '0 0 15px var(--danger)' : '0 0 10px rgba(0, 196, 255, 0.3)'
            }}
          >
            {isAutoPilot ? <Activity size={18} className="spin-slow" /> : <Activity size={18} />}
            {isAutoPilot ? t('queue_status', { count: queueSize }) : t('auto_pilot_off')}
          </button>

          <div style={{ display: 'flex', gap: '0.5rem', marginLeft: '1rem' }}>
            <button className="icon-button" onClick={() => changeLanguage('kz')} title="Қаз 🇰🇿" style={{ borderColor: i18n.language === 'kz' ? 'var(--accent)' : 'var(--border-color)', opacity: i18n.language === 'kz' ? 1 : 0.6 }}>🇰🇿</button>
            <button className="icon-button" onClick={() => changeLanguage('ru')} title="Рус 🇷🇺" style={{ borderColor: i18n.language === 'ru' ? 'var(--accent)' : 'var(--border-color)', opacity: i18n.language === 'ru' ? 1 : 0.6 }}>🇷🇺</button>
            <button className="icon-button" onClick={() => changeLanguage('en')} title="Eng 🇬🇧" style={{ borderColor: i18n.language === 'en' ? 'var(--accent)' : 'var(--border-color)', opacity: i18n.language === 'en' ? 1 : 0.6 }}>🇬🇧</button>
          </div>

          <button className="icon-button" title={t('theme_toggle')} onClick={() => setIsDarkTheme(!isDarkTheme)} style={{ marginLeft: '0.5rem' }}>
            {isDarkTheme ? <Sun size={20} /> : <Moon size={20} />}
          </button>

          <select 
            className="form-select" value={activeProfileId || ''} 
            onChange={e => setActiveProfileId(parseInt(e.target.value))} style={{ marginLeft: '0.5rem' }}
          >
            {profiles.map(p => <option key={p.id} value={p.id}>{getProfileTranslation(p.name)}</option>)}
          </select>
        </div>
      </header>

      <main className="main-content">
        {currentView === 'feed' && (
          <>
            {!focusMode && (
            <div className="platform-filters" style={{ display: 'flex', gap: '1rem', marginBottom: '2rem', flexWrap: 'wrap', background: 'var(--panel-bg)', padding: '1rem', borderRadius: '12px', border: '1px solid var(--border-color)' }}>
              {[
                { id: 'all', icon: <Globe size={18} />, label: t('filter_all') },
                { id: 'youtube', icon: SVG_YOUTUBE, label: 'YouTube' },
                { id: 'telegram', icon: SVG_TELEGRAM, label: 'Telegram' },
                { id: 'vk', icon: SVG_VK, label: 'VK' },
              ].map(platform => (
                <button
                  key={platform.id} onClick={() => setPlatformFilter(platform.id)}
                  style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', padding: '0.5rem 1rem', borderRadius: '8px', border: 'none', cursor: 'pointer', background: platformFilter === platform.id ? 'var(--accent)' : 'transparent', color: platformFilter === platform.id ? '#fff' : 'var(--text-secondary)', fontWeight: platformFilter === platform.id ? 'bold' : 'normal', transition: 'all 0.2s ease' }}
                >
                  {platform.icon} {platform.label}
                </button>
              ))}
            </div>
            )}

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '2rem' }}>
              <h2 style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Video color="var(--accent)" /> {t('live_feed')}
                {isAutoPilot && <span style={{ fontSize: '0.8rem', color: 'var(--danger)', marginLeft: '1rem', fontWeight: 'normal' }}>🔴 {t('live_scanning')}</span>}
                <button onClick={handleClearHistory} style={{ marginLeft: '1rem', background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--text-secondary)', padding: '0.3rem 0.6rem', borderRadius: '6px', cursor: 'pointer', fontSize: '0.8rem' }}>{t('clear')}</button>
              </h2>
              
              <div style={{ display: 'flex', gap: '1rem', flex: 1, maxWidth: '700px', marginLeft: '2rem' }}>
                <input 
                  type="text" className="form-select" style={{ flex: 1, padding: '0.75rem 1rem' }}
                  placeholder={t('url_placeholder')} value={urlInput}
                  onChange={(e) => setUrlInput(e.target.value)} onKeyDown={(e) => { if (e.key === 'Enter') handleAnalyzeUrl(); }}
                  disabled={isSimulating}
                />
                <button 
                  className="action-button" onClick={handleAnalyzeUrl} disabled={isSimulating || !urlInput}
                  style={{ background: 'var(--panel-bg)', border: '1px solid var(--accent)', color: 'var(--text-primary)', padding: '0.6rem 1.2rem', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  {isSimulating ? <div className="loader" style={{width: '16px', height: '16px', borderTopColor: 'var(--accent)'}}></div> : <Play size={18} color="var(--accent)" />}
                  {isSimulating ? t('simulating') : t('simulate_new')}
                </button>
                
                <input type="file" accept="audio/*" ref={audioInputRef} style={{ display: 'none' }} onChange={handleAudioUpload} />
                <button 
                  className="action-button" onClick={() => audioInputRef.current?.click()} disabled={isAudioUploading}
                  style={{ background: 'var(--panel-bg)', border: '1px solid var(--accent)', color: 'var(--text-primary)', padding: '0.6rem 1.2rem', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem' }}
                >
                  {isAudioUploading ? <div className="loader" style={{width: '16px', height: '16px', borderTopColor: 'var(--accent)'}}></div> : <Mic size={18} color="var(--accent)" />}
                  {t('analyze_audio')}
                </button>
              </div>
            </div>

            {focusMode && (
              <button onClick={exitFocusMode} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', padding: '0.7rem 1.4rem', borderRadius: '10px', border: '1px solid var(--accent)', background: 'var(--panel-bg)', color: 'var(--accent)', cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem', boxShadow: '0 0 12px rgba(0,196,255,0.15)', transition: 'all 0.2s ease' }}>
                <ArrowLeft size={18} /> {t('focus_show_all')}
              </button>
            )}

            {focusMode && !focusResultId && (
              <div style={{ background: 'var(--panel-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '3rem', textAlign: 'center', maxWidth: '600px', margin: '0 auto' }}>
                {!focusTimedOut ? (
                  <>
                    <div className="loader" style={{ margin: '0 auto 1.5rem' }}></div>
                    <p style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '0.75rem' }}>{t('focus_loading')}</p>
                    <p style={{ color: 'var(--text-secondary)', wordBreak: 'break-all', fontSize: '0.85rem' }}>{focusTarget}</p>
                  </>
                ) : (
                  <>
                    <AlertTriangle size={36} color="var(--flag-color)" style={{ marginBottom: '1rem' }} />
                    <p style={{ fontSize: '1.1rem', fontWeight: 600, marginBottom: '1rem' }}>{t('focus_timeout')}</p>
                    <p style={{ color: 'var(--text-secondary)', wordBreak: 'break-all', fontSize: '0.85rem', marginBottom: '1.5rem' }}>{focusTarget}</p>
                    <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
                      <button onClick={() => { setFocusTimedOut(false); focusTimerRef.current = setTimeout(() => setFocusTimedOut(true), 60000); }} style={{ padding: '0.6rem 1.4rem', borderRadius: '8px', border: '1px solid var(--accent)', background: 'var(--accent)', color: '#fff', cursor: 'pointer', fontWeight: 600 }}>
                        {t('focus_retry')}
                      </button>
                      <button onClick={exitFocusMode} style={{ padding: '0.6rem 1.4rem', borderRadius: '8px', border: '1px solid var(--border-color)', background: 'var(--panel-bg)', color: 'var(--text-primary)', cursor: 'pointer', fontWeight: 600 }}>
                        {t('focus_show_all')}
                      </button>
                    </div>
                  </>
                )}
              </div>
            )}

            <div className="feed-grid">
              {feedItems.length === 0 && !isAutoPilot && !focusMode ? (
                <div style={{ textAlign: 'center', padding: '4rem', color: 'var(--text-secondary)', gridColumn: '1 / -1' }}>
                  <Activity size={48} style={{ opacity: 0.3, marginBottom: '1rem' }} />
                  <p style={{ fontSize: '1.1rem' }}>{t('empty_feed')}</p>
                </div>
              ) : feedItems.filter(item => {
                if (focusMode) return focusResultId && item.id === focusResultId;
                if (platformFilter === 'all') return true;
                if (!item.url) return platformFilter === 'telegram';
                const url = item.url.toLowerCase();
                if (platformFilter === 'youtube') return url.includes('youtube.com') || url.includes('youtu.be');
                if (platformFilter === 'tiktok') return url.includes('tiktok.com');
                if (platformFilter === 'telegram') return url.includes('t.me');
                if (platformFilter === 'vk') return url.includes('vk.com');
                return true;
              }).map(item => renderCard(item, feedResults[item.id], true))}
            </div>
          </>
        )}

        {currentView === 'profile' && (
          <div>
            <button onClick={() => setCurrentView('feed')} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', padding: '0.7rem 1.4rem', borderRadius: '10px', border: '1px solid var(--accent)', background: 'var(--panel-bg)', color: 'var(--accent)', cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem' }}>
              <ArrowLeft size={18} /> {t('back_to_feed')}
            </button>
            
            {isProfileLoading ? (
              <div style={{ textAlign: 'center', padding: '4rem' }}>
                <div className="loader" style={{ margin: '0 auto 1.5rem' }}></div>
                <p>{t('profile_loading')}</p>
              </div>
            ) : profileData && (
              <>
                <div style={{ background: 'var(--panel-bg)', padding: '2rem', borderRadius: '16px', border: '1px solid var(--border-color)', marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <h2 style={{ margin: '0 0 0.5rem 0', display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <User size={28} color="var(--accent)"/> {profileData.account.handle}
                    </h2>
                    <p style={{ color: 'var(--text-secondary)', margin: 0 }}>
                      {t('platform')}: <b>{profileData.account.platform}</b> | 
                      {t('posts_analyzed')}: <b>{profileData.account.total_analyzed}</b>
                    </p>
                    {profileData.account.url && (
                      <a href={profileData.account.url} target="_blank" rel="noreferrer" style={{ color: 'var(--accent)', display: 'inline-block', marginTop: '0.5rem' }}>
                        {t('open_profile')}
                      </a>
                    )}
                  </div>
                  <div style={{ textAlign: 'center', background: 'var(--bg-color)', padding: '1rem 2rem', borderRadius: '12px', border: `2px solid ${profileData.account.avg_risk > 0.5 ? 'var(--block-color)' : 'var(--accent)'}` }}>
                    <p style={{ margin: '0 0 0.5rem 0', fontSize: '0.9rem', color: 'var(--text-secondary)' }}>{t('average_risk_score')}</p>
                    <h1 style={{ margin: 0, color: profileData.account.avg_risk > 0.5 ? 'var(--block-color)' : 'var(--accent)' }}>
                      {Math.round(profileData.account.avg_risk * 100)}%
                    </h1>
                  </div>
                </div>
                
                <h3>{t('top_risk_posts')}</h3>
                <div className="feed-grid">
                  {profileData.items.map(item => renderCard(item, {
                    decision: item.decision,
                    scores: item.scores,
                    explanation: item.explanation,
                    risk_score: item.risk_score
                  }, false))}
                </div>
              </>
            )}
          </div>
        )}

        {currentView === 'settings' && (
          <div>
            <button onClick={() => setCurrentView('feed')} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', padding: '0.7rem 1.4rem', borderRadius: '10px', border: '1px solid var(--accent)', background: 'var(--panel-bg)', color: 'var(--accent)', cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem' }}>
              <ArrowLeft size={18} /> {t('back_to_feed')}
            </button>

            <div style={{ display: 'grid', gridTemplateColumns: 'minmax(320px, 1fr) minmax(320px, 1fr)', gap: '1.5rem', alignItems: 'start' }}>
              <section style={{ background: 'var(--panel-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '1.5rem' }}>
                <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Settings size={22} color="var(--accent)" /> {t('moderation_profile')}</h2>
                {profileDraft && (
                  <>
                    <input
                      className="form-select"
                      value={profileDraft.name}
                      onChange={e => setProfileDraft(prev => ({ ...prev, name: e.target.value }))}
                      disabled={BUILTIN_PROFILE_NAMES.has(profiles.find(p => p.id === profileDraft.id)?.name)}
                      style={{ width: '100%', marginBottom: '1rem', padding: '0.75rem 1rem' }}
                    />
                    {Object.entries(profileDraft.thresholds).map(([key, value]) => (
                      <label key={key} style={{ display: 'grid', gridTemplateColumns: '1fr 72px', gap: '1rem', alignItems: 'center', marginBottom: '0.9rem' }}>
                        <span style={{ fontWeight: 600 }}>{getCategoryTranslation(key)}</span>
                        <input
                          className="form-select"
                          type="number"
                          min="0"
                          max="1"
                          step="0.01"
                          value={value}
                          onChange={e => handleThresholdChange(key, e.target.value)}
                          style={{ padding: '0.45rem' }}
                        />
                      </label>
                    ))}
                    <button onClick={handleSaveProfile} disabled={isSettingsSaving} style={{ marginTop: '0.5rem', background: 'var(--accent)', border: 'none', color: '#fff', padding: '0.7rem 1.2rem', borderRadius: '8px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.5rem', fontWeight: 700 }}>
                      <Save size={18} /> {isSettingsSaving ? t('saving') : t('save_profile')}
                    </button>
                  </>
                )}
              </section>

              <section style={{ background: 'var(--panel-bg)', border: '1px solid var(--border-color)', borderRadius: '16px', padding: '1.5rem' }}>
                <h2 style={{ marginTop: 0, display: 'flex', alignItems: 'center', gap: '0.5rem' }}><Activity size={22} color="var(--accent)" /> {t('watchlist')}</h2>
                <div style={{ display: 'grid', gridTemplateColumns: '120px 1fr auto', gap: '0.75rem', marginBottom: '1rem' }}>
                  <select className="form-select" value={watchPlatform} onChange={e => setWatchPlatform(e.target.value)}>
                    <option value="youtube">YouTube</option>
                    <option value="telegram">Telegram</option>
                    <option value="vk">VK</option>
                  </select>
                  <input className="form-select" value={watchTarget} onChange={e => setWatchTarget(e.target.value)} placeholder={t('watch_target_placeholder')} />
                  <button onClick={handleAddWatchTarget} style={{ background: 'var(--accent)', border: 'none', color: '#fff', padding: '0.6rem 0.9rem', borderRadius: '8px', cursor: 'pointer' }} title={t('add_watch_target')}>
                    <Plus size={18} />
                  </button>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                  {watchlist.map(item => (
                    <div key={item.id} style={{ display: 'grid', gridTemplateColumns: '110px 1fr auto', gap: '0.75rem', alignItems: 'center', background: 'var(--bg-color)', padding: '0.75rem', borderRadius: '8px', border: '1px solid var(--border-color)' }}>
                      <strong>{item.platform}</strong>
                      <span style={{ wordBreak: 'break-word' }}>{item.target}</span>
                      <button onClick={() => handleDeleteWatchTarget(item.id)} style={{ background: 'transparent', border: '1px solid var(--border-color)', color: 'var(--block-color)', padding: '0.45rem', borderRadius: '8px', cursor: 'pointer' }} title={t('delete_watch_target')}>
                        <Trash2 size={16} />
                      </button>
                    </div>
                  ))}
                  {watchlist.length === 0 && <p style={{ color: 'var(--text-secondary)' }}>{t('no_watch_targets')}</p>}
                </div>
              </section>
            </div>
          </div>
        )}
        
        {currentView === 'graph' && (
          <div style={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
            <button onClick={() => setCurrentView('feed')} style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1.5rem', padding: '0.7rem 1.4rem', borderRadius: '10px', border: '1px solid var(--accent)', background: 'var(--panel-bg)', color: 'var(--accent)', cursor: 'pointer', fontWeight: 600, fontSize: '0.95rem', width: 'fit-content' }}>
              <ArrowLeft size={18} /> {t('back_to_feed')}
            </button>
            
            <div style={{ flex: 1, background: 'var(--panel-bg)', borderRadius: '16px', border: '1px solid var(--border-color)', position: 'relative', overflow: 'hidden' }} ref={graphContainerRef}>
              {isGraphLoading ? (
                <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', height: '100%' }}>
                  <div className="loader" style={{ margin: '0 auto 1.5rem' }}></div>
                  <p>{t('graph_loading')}</p>
                </div>
              ) : (
                <>
                  <div style={{ position: 'absolute', top: 20, left: 20, zIndex: 10, background: 'rgba(0,0,0,0.6)', padding: '1rem', borderRadius: '8px', color: '#fff', fontSize: '0.85rem' }}>
                    <h4 style={{ margin: '0 0 0.5rem 0' }}>{t('connection_graph')}</h4>
                    <p style={{ margin: '0 0 0.5rem 0' }}>{t('graph_nodes_help')}</p>
                    <p style={{ margin: 0 }}>{t('graph_edges_help')}</p>
                  </div>
                  <ForceGraph2D
                    width={graphDimensions.width}
                    height={graphDimensions.height}
                    graphData={graphData}
                    nodeLabel={node => `${node.id} (${node.platform}) | Risk: ${Math.round(node.avg_risk*100)}%`}
                    nodeVal={node => node.post_count * 2 + 5}
                    nodeColor={node => {
                      if (node.avg_risk >= 0.55) return '#ef4444'; // block
                      if (node.avg_risk >= 0.30) return '#f59e0b'; // flag
                      return '#10b981'; // allow
                    }}
                    linkLabel={link => `${t('shared')}: ${link.shared.join(', ')}`}
                    linkWidth={2}
                    linkColor={() => 'rgba(255, 255, 255, 0.2)'}
                    backgroundColor={isDarkTheme ? '#0b1121' : '#f8fafc'}
                  />
                </>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}

export default App;
