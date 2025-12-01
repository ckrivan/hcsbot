import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './index.css';

// Use relative API routes for Vercel deployment
const API_BASE_URL = process.env.NODE_ENV === 'production'
  ? '/api'
  : (process.env.REACT_APP_API_URL || 'http://localhost:8000');

const DEBUG_MODE = process.env.NODE_ENV === 'development' || window.location.search.includes('debug=true');

// Cache busting version for static assets
const ASSET_VERSION = '2.0.20251120';

// Debug logging
console.log('Environment Info:', {
  NODE_ENV: process.env.NODE_ENV,
  REACT_APP_API_URL: process.env.REACT_APP_API_URL,
  API_BASE_URL
});

function App() {
  const [messages, setMessages] = useState([]);
  const [inputText, setInputText] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [systemStatus, setSystemStatus] = useState('initializing');
  const [sampleQuestions, setSampleQuestions] = useState([]);
  const [showSampleQuestions, setShowSampleQuestions] = useState(false);
  const [showAdmin, setShowAdmin] = useState(false);
  const [adminLoggedIn, setAdminLoggedIn] = useState(false);
  const [feedbackData, setFeedbackData] = useState([]);
  const [showChangelog, setShowChangelog] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(true);
  const [passwordInput, setPasswordInput] = useState('');
  const [authError, setAuthError] = useState('');
  const [showDisclaimer, setShowDisclaimer] = useState(false);
  const [disclaimerAccepted, setDisclaimerAccepted] = useState(false);
  const messagesEndRef = useRef(null);

  // Password configuration - handles spaces and special characters
  const APP_PASSWORD = process.env.REACT_APP_ACCESS_PASSWORD || 'I L0V3 P!ZZ@$$$';

  // Version tracking for changelog
  const CURRENT_VERSION = "1.4.0";
  const CHANGELOG = {
    "1.4.0": {
      title: "Multi-Domain Knowledge Sources",
      date: "2025-12-01",
      features: [
        "Expanded knowledge sources beyond HCS documentation",
        "Searches 4 external domains when HCS docs don't have answers:",
        "   • Jamf Nation community discussions",
        "   • Official Jamf documentation (jamf.com)",
        "   • Apple Support articles",
        "   • Apple Developer documentation",
        "Smart fallback with low-confidence detection (< 0.3 similarity)",
        "Direct links to original sources with proper attribution",
        "Google Custom Search API integration for reliable results",
        "Separate content extraction for community threads vs docs",
        "Dynamic source labeling in bot responses"
      ]
    },
    "1.3.0": {
      title: "Apple Style Guide Integration",
      date: "2025-08-21",
      features: [
        "Official Apple Style Guide integrated into knowledge base",
        "Authoritative Apple terminology guidance (3,276 searchable chunks)",
        "Correct usage for \"sign-in window\" vs \"login window\"",
        "\"System Settings\" vs \"System Preferences\" clarification",
        "Apple interface conventions and style standards",
        "System reload functionality for processing new documents"
      ]
    },
    "1.2.0": {
      title: "Enhanced Search Quality & Admin Dashboard",
      date: "2025-08-21",
      features: [
        "Much smarter search filtering - no more irrelevant results",
        "Automatic detection of unsupported topics (Jamf Security Portal, etc.)",
        "Admin dashboard to view user feedback",
        "Persistent feedback storage across restarts",
        "Clickable suggested questions with visual indicators",
        "Improved similarity threshold (0.4) for better accuracy"
      ]
    }
  };

  const scrollToBottom = () => {
    // Use setTimeout to ensure DOM has updated before scrolling
    setTimeout(() => {
      if (messagesEndRef.current) {
        // Use instant scroll on mobile for better reliability
        const isMobile = window.innerWidth <= 768;
        messagesEndRef.current.scrollIntoView({
          behavior: isMobile ? 'auto' : 'smooth',
          block: 'end',
          inline: 'nearest'
        });
      }
    }, 100);
  };

  useEffect(() => {
    // Only auto-scroll if there's more than just the welcome message
    // This prevents scrolling past the welcome message on mobile
    if (messages.length > 1) {
      scrollToBottom();
    }
  }, [messages]);

  // Check for existing authentication session
  useEffect(() => {
    const savedAuth = sessionStorage.getItem('hcs_authenticated');
    if (savedAuth === 'true') {
      setIsAuthenticated(true);
    }
  }, []);

  // Show disclaimer on every visit
  useEffect(() => {
    if (isAuthenticated) {
      setShowDisclaimer(true);
    }
  }, [isAuthenticated]);

  useEffect(() => {
    if (isAuthenticated) {
      // Always check system health, regardless of disclaimer
      checkSystemHealth();
      fetchSampleQuestions();

      // Only show chat interface if disclaimer accepted
      if (!disclaimerAccepted) {
        return; // Don't set welcome message until disclaimer accepted
      }

      // Initial welcome message - only set if messages array is empty
      setMessages(prevMessages => {
        if (prevMessages.length === 0) {
          return [
            {
              type: 'assistant',
              content:
                "Hello! I'm Corby, your HCS Technology Group assistant. I can help you with questions about Apple device management, Jamf Pro, iOS deployment, and more based on our comprehensive documentation.",
              sources: [],
              timestamp: Date.now(),
            },
          ];
        }
        return prevMessages;
      });
    }
  }, [isAuthenticated, disclaimerAccepted]);

  // Mobile-friendly API call with fallback
  const makeApiCall = async (url, options = {}) => {
    // First try with axios
    try {
      return await axios.get(url, {
        timeout: 10000,
        headers: {
          'Content-Type': 'application/json',
          'Accept': 'application/json',
        },
        ...options
      });
    } catch (axiosError) {
      console.warn('Axios failed, trying fetch:', axiosError.message);
      
      // Fallback to fetch for iOS Safari
      try {
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json',
          },
          mode: 'cors',
          credentials: 'omit', // Don't send credentials for mobile compatibility
        });
        
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const data = await response.json();
        return { data }; // Mimic axios response structure
      } catch (fetchError) {
        console.error('Fetch also failed:', fetchError);
        throw fetchError;
      }
    }
  };

  const checkSystemHealth = async () => {
    try {
      console.log('Checking system health at:', `${API_BASE_URL}/health`);
      console.log('User agent:', navigator.userAgent);
      
      const response = await makeApiCall(`${API_BASE_URL}/health`);
      setSystemStatus(response.data.initialized ? 'ready' : 'initializing');
      console.log('System health check successful:', response.data);
    } catch (error) {
      console.error('Health check failed:', error);
      console.error('API URL:', API_BASE_URL);
      console.error('Error details:', error.response || error.message);
      console.error('Full error object:', error);
      
      setSystemStatus('error');
    }
  };

  const fetchSampleQuestions = async () => {
    try {
      const response = await axios.get(`${API_BASE_URL}/sample-questions`);
      setSampleQuestions(response.data.questions || []);
    } catch (error) {
      console.error('Failed to fetch sample questions:', error);
    }
  };

  const sendMessage = async text => {
    if (!text.trim() || isLoading) return;

    const userMessage = {
      type: 'user',
      content: text,
      sources: [],
    };

    setMessages(prev => [...prev, userMessage]);
    setInputText('');
    setIsLoading(true);

    try {
      const response = await axios.post(`${API_BASE_URL}/chat`, {
        question: text,
      });

      console.log('Received sources:', response.data.sources); // Debug log

      const assistantMessage = {
        type: 'assistant',
        content: response.data.answer,
        sources: response.data.sources || [],
        timestamp: Date.now(), // Add timestamp to ensure unique rendering
        query: text, // Store the original query for feedback
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Chat error:', error);

      let errorMessage =
        'I apologize, but I encountered an error processing your question.';

      if (error.response?.status === 503) {
        errorMessage =
          'The system is still initializing. Please wait a moment and try again.';
      } else if (error.response?.data?.detail) {
        errorMessage = error.response.data.detail;
      }

      const errorResponse = {
        type: 'assistant',
        content: errorMessage,
        sources: [],
        timestamp: Date.now(), // Add timestamp to ensure unique rendering
      };

      setMessages(prev => [...prev, errorResponse]);
    } finally {
      setIsLoading(false);
    }
  };

  const submitFeedback = async (query, response, feedbackType, description) => {
    try {
      await axios.post(`${API_BASE_URL}/feedback`, {
        query,
        response,
        feedback_type: feedbackType,
        description
      });
      alert('Thank you for your feedback!');
    } catch (error) {
      console.error('Feedback error:', error);
      alert('Error submitting feedback. Please try again.');
    }
  };

  const adminLogin = async (username, password) => {
    try {
      await axios.post(`${API_BASE_URL}/admin/login`, { username, password });
      setAdminLoggedIn(true);
      await loadFeedbackData(username, password);
    } catch (error) {
      alert('Invalid credentials');
    }
  };

  const loadFeedbackData = async (username = 'hcs', password = 'I love P!zz@') => {
    try {
      const response = await axios.get(`${API_BASE_URL}/admin/feedback?username=${username}&password=${password}`);
      setFeedbackData(response.data.feedback);
    } catch (error) {
      console.error('Error loading feedback:', error);
    }
  };

  // Check for admin access via URL hash and version updates
  useEffect(() => {
    const checkHash = () => {
      const hash = window.location.hash;
      if (hash === '#admin') {
        setShowAdmin(true);
      } else if (hash === '#changelog') {
        setShowChangelog(true);
      }
    };
    
    // Check on mount
    checkHash();
    
    // Listen for hash changes
    window.addEventListener('hashchange', checkHash);
    
    // Check if user has seen the latest changelog (only for new visits)
    const lastSeenVersion = localStorage.getItem('lastSeenVersion');
    if (!lastSeenVersion || lastSeenVersion !== CURRENT_VERSION) {
      // Show changelog after a short delay to avoid overwhelming users
      setTimeout(() => setShowChangelog(true), 2000);
    }
    
    // Cleanup
    return () => window.removeEventListener('hashchange', checkHash);
  }, []);

  const acceptDisclaimer = () => {
    setDisclaimerAccepted(true);
    setShowDisclaimer(false);
  };

  const handleSubmit = e => {
    e.preventDefault();
    sendMessage(inputText);
  };

  const handleSampleQuestion = question => {
    sendMessage(question);
  };

  const handleKeyPress = e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Authentication functions
  const handlePasswordSubmit = (e) => {
    e.preventDefault();
    if (passwordInput === APP_PASSWORD) {
      setIsAuthenticated(true);
      sessionStorage.setItem('hcs_authenticated', 'true');
      setAuthError('');
      setPasswordInput('');
    } else {
      setAuthError('Invalid password. Please try again.');
      setPasswordInput('');
    }
  };

  const handleSignOut = () => {
    setIsAuthenticated(false);
    sessionStorage.removeItem('hcs_authenticated');
    setMessages([]);
    setPasswordInput('');
    setAuthError('');
  };

  const handlePasswordKeyPress = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handlePasswordSubmit(e);
    }
  };

  // No longer needed - using ReactMarkdown instead
  // const formatContent = content => { ... }

  const renderMessage = (message, index) => {
    // Add click handler to the message div to catch clicks on numbered questions
    const handleMessageClick = (e) => {
      // Get the clicked element's text content
      const clickedText = e.target.textContent || e.target.innerText || '';
      
      // Check if clicked text looks like a numbered question
      const questionMatch = clickedText.match(/^\d+\.\s*(.+\?)$/);
      if (questionMatch) {
        const questionText = questionMatch[1].trim();
        sendMessage(questionText);
        e.stopPropagation();
      }
    };

    return (
      <div
        key={`${index}-${message.timestamp || index}`}
        className={`message ${message.type}`}
        onClick={handleMessageClick}
        style={{cursor: 'default'}}
      >
        <div className="content formatted-content">
          <ReactMarkdown 
            remarkPlugins={[remarkGfm]}
            components={{
            // Custom styling for markdown elements
            h1: ({node, ...props}) => <h1 style={{color: '#1f2937', marginBottom: '0.5rem'}} {...props} />,
            h2: ({node, ...props}) => <h2 style={{color: '#374151', marginBottom: '0.5rem', borderBottom: '2px solid #e5e7eb', paddingBottom: '0.25rem'}} {...props} />,
            h3: ({node, ...props}) => <h3 style={{color: '#4b5563', marginBottom: '0.5rem'}} {...props} />,
            code: ({node, inline, ...props}) =>
              inline ? (
                <code style={{backgroundColor: '#f3f4f6', padding: '0.125rem 0.25rem', borderRadius: '0.25rem', fontSize: '0.875rem', whiteSpace: 'nowrap', display: 'inline', wordBreak: 'keep-all'}} {...props} />
              ) : (
                <pre style={{backgroundColor: '#f8fafc', padding: '1rem', borderRadius: '0.5rem', border: '1px solid #e2e8f0', overflow: 'auto'}}>
                  <code {...props} />
                </pre>
              ),
            blockquote: ({node, ...props}) => <blockquote style={{borderLeft: '4px solid #3b82f6', paddingLeft: '1rem', margin: '1rem 0', fontStyle: 'italic'}} {...props} />,
            ul: ({node, ...props}) => <ul style={{paddingLeft: '1.5rem', marginBottom: '0.5rem'}} {...props} />,
            ol: ({node, ...props}) => <ol style={{paddingLeft: '1.5rem', marginBottom: '0.5rem'}} {...props} />,
            li: ({node, ...props}) => {
              // Check if this list item contains a question that should be clickable
              const children = props.children;
              const text = Array.isArray(children) ? children.join('') : children;
              
              // Check if it looks like a question (ends with ?)
              if (typeof text === 'string' && text.trim().endsWith('?')) {
                return (
                  <li 
                    style={{
                      marginBottom: '0.5rem',
                      cursor: 'pointer',
                      padding: '0.75rem',
                      borderRadius: '0.5rem',
                      border: '2px solid #3b82f6',
                      backgroundColor: '#eff6ff',
                      transition: 'all 0.2s ease',
                      listStyle: 'none',
                      boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
                    }}
                    onMouseEnter={(e) => {
                      e.target.style.backgroundColor = '#dbeafe';
                      e.target.style.borderColor = '#2563eb';
                      e.target.style.transform = 'translateY(-1px)';
                    }}
                    onMouseLeave={(e) => {
                      e.target.style.backgroundColor = '#eff6ff';
                      e.target.style.borderColor = '#3b82f6';
                      e.target.style.transform = 'translateY(0px)';
                    }}
                  >
                    <span style={{fontWeight: '500'}}>{children}</span>
                    <span style={{
                      color: '#3b82f6', 
                      fontSize: '0.875rem', 
                      marginLeft: '0.5rem',
                      fontWeight: '500'
                    }}>👆 Click to ask!</span>
                  </li>
                );
              }
              
              return <li style={{marginBottom: '0.25rem'}} {...props} />;
            },
            hr: ({node, ...props}) => <hr style={{margin: '1.5rem 0', border: 'none', borderTop: '2px solid #e5e7eb'}} {...props} />,
            strong: ({node, ...props}) => <strong style={{fontWeight: '600', color: '#1f2937'}} {...props} />,
            p: ({node, ...props}) => {
              // Check if this paragraph contains a numbered question that could be clickable
              const children = props.children;
              
              // Handle case where the paragraph contains multiple children (like "1. " followed by question text)
              if (Array.isArray(children) && children.length >= 2) {
                const firstChild = children[0];
                const secondChild = children[1];
                
                // Check if first child is a number pattern like "1. " and second is the question text
                if (typeof firstChild === 'string' && typeof secondChild === 'string' && 
                    /^\d+\.\s*$/.test(firstChild)) {
                  const questionText = secondChild.trim();
                  const numberPart = firstChild.trim();
                  
                  return (
                    <p 
                      style={{
                        marginBottom: '0.75rem', 
                        lineHeight: '1.6',
                        cursor: 'pointer',
                        padding: '0.5rem',
                        borderRadius: '0.375rem',
                        border: '1px solid #e5e7eb',
                        backgroundColor: '#f9fafb',
                        transition: 'all 0.2s ease'
                      }}
                      onClick={() => {
                        sendMessage(questionText);
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.backgroundColor = '#f3f4f6';
                        e.target.style.borderColor = '#3b82f6';
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.backgroundColor = '#f9fafb';
                        e.target.style.borderColor = '#e5e7eb';
                      }}
                    >
                      <strong>{numberPart}</strong> {questionText}
                      <span style={{color: '#6b7280', fontSize: '0.875rem', marginLeft: '0.5rem'}}>👆 Click to ask</span>
                    </p>
                  );
                }
              }
              
              // Also check for single string format
              const text = children?.[0];
              if (typeof text === 'string') {
                // Match both **1.** and 1. formats
                const boldNumberMatch = text.match(/^\*\*\d+\.\*\*\s*(.+)$/);
                const regularNumberMatch = text.match(/^\d+\.\s*(.+)$/);
                
                if (boldNumberMatch || regularNumberMatch) {
                  const questionText = boldNumberMatch ? boldNumberMatch[1] : regularNumberMatch[1];
                  const numberPart = boldNumberMatch ? 
                    text.match(/^\*\*\d+\.\*\*/)[0].replace(/\*\*/g, '') : 
                    text.match(/^\d+\./)[0];
                  
                  return (
                    <p 
                      style={{
                        marginBottom: '0.75rem', 
                        lineHeight: '1.6',
                        cursor: 'pointer',
                        padding: '0.5rem',
                        borderRadius: '0.375rem',
                        border: '1px solid #e5e7eb',
                        backgroundColor: '#f9fafb',
                        transition: 'all 0.2s ease'
                      }}
                      onClick={() => {
                        sendMessage(questionText);
                      }}
                      onMouseEnter={(e) => {
                        e.target.style.backgroundColor = '#f3f4f6';
                        e.target.style.borderColor = '#3b82f6';
                      }}
                      onMouseLeave={(e) => {
                        e.target.style.backgroundColor = '#f9fafb';
                        e.target.style.borderColor = '#e5e7eb';
                      }}
                    >
                      <strong>{numberPart}</strong> {questionText}
                      <span style={{color: '#6b7280', fontSize: '0.875rem', marginLeft: '0.5rem'}}>👆 Click to ask</span>
                    </p>
                  );
                }
              }
              return <p style={{marginBottom: '0.75rem', lineHeight: '1.6'}} {...props} />;
            }
          }}
        >
          {message.content}
        </ReactMarkdown>
      </div>
      {message.sources && message.sources.length > 0 && (
        <div className="sources">
          <strong>Sources:</strong>
          {message.sources.map((source, idx) => (
            <div
              key={`${source.filename}-${source.page_number}-${idx}`}
              className="source-item"
            >
              <a
                href={source.url || `https://hcsonline.com/images/PDFs/${source.filename}${source.page_number ? `#page=${source.page_number}` : ''}`}
                target="_blank"
                rel="noopener noreferrer"
                className="source-filename"
              >
                {source.filename}
              </a>
              <span className="source-page">{source.page_number ? `Page ${source.page_number}` : ''} ↗</span>
            </div>
          ))}
        </div>
      )}
      {message.type === 'assistant' && (
        <div style={{marginTop: '0.5rem', textAlign: 'right'}}>
          <a
            href="mailto:ckrivan@hcsonline.com?subject=HCSBot%20Feedback"
            style={{
              fontSize: '0.75rem',
              padding: '0.25rem 0.5rem',
              background: '#f3f4f6',
              border: '1px solid #d1d5db',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              color: '#6b7280',
              textDecoration: 'none',
              display: 'inline-block'
            }}
          >
            📝 Feedback
          </a>
        </div>
      )}
      </div>
    );
  };

  // Password Protection Component
  const PasswordLogin = () => {
    return (
      <div className="container">
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          minHeight: '100vh',
          padding: '2rem'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '1rem',
            padding: '3rem',
            boxShadow: '0 10px 25px rgba(0, 0, 0, 0.1)',
            maxWidth: '500px',
            width: '100%',
            textAlign: 'center'
          }}>
            <div style={{ marginBottom: '2rem' }}>
              <img src={`/hcs-logo.png?v=${ASSET_VERSION}`} alt="HCS Logo" style={{
                height: '100px',
                marginBottom: '1rem',
                filter: 'drop-shadow(0 2px 4px rgba(0,0,0,0.1))'
              }} />
              <h1 style={{
                color: '#1f2937',
                marginBottom: '0.5rem',
                fontSize: '2rem',
                fontWeight: '600'
              }}>
                HCS Technology Group Corby
              </h1>
              <p style={{
                color: '#6b7280',
                fontSize: '1.1rem',
                margin: '0'
              }}>
                Enter access code to continue
              </p>
            </div>
            
            <form onSubmit={handlePasswordSubmit} style={{ marginBottom: '1rem' }}>
              <input
                type="password"
                placeholder="Enter password"
                value={passwordInput}
                onChange={(e) => setPasswordInput(e.target.value)}
                onKeyPress={handlePasswordKeyPress}
                style={{
                  width: '100%',
                  padding: '1rem',
                  fontSize: '1.1rem',
                  border: '2px solid #e5e7eb',
                  borderRadius: '0.5rem',
                  marginBottom: '1rem',
                  textAlign: 'center',
                  outline: 'none',
                  transition: 'border-color 0.2s ease',
                  ...(authError && { borderColor: '#dc2626' })
                }}
                onFocus={(e) => e.target.style.borderColor = '#3b82f6'}
                onBlur={(e) => e.target.style.borderColor = authError ? '#dc2626' : '#e5e7eb'}
                autoFocus
              />
              <button 
                type="submit" 
                style={{
                  width: '100%',
                  padding: '1rem',
                  fontSize: '1.1rem',
                  fontWeight: '500',
                  backgroundColor: '#3b82f6',
                  color: 'white',
                  border: 'none',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  transition: 'background-color 0.2s ease'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = '#2563eb'}
                onMouseOut={(e) => e.target.style.backgroundColor = '#3b82f6'}
              >
                Access Chatbot
              </button>
            </form>
            
            {authError && (
              <div style={{
                backgroundColor: '#fef2f2',
                color: '#dc2626',
                padding: '0.75rem',
                borderRadius: '0.5rem',
                fontSize: '0.875rem',
                border: '1px solid #fecaca'
              }}>
                {authError}
              </div>
            )}
            
            <div style={{ marginTop: '2rem', fontSize: '0.875rem', color: '#9ca3af' }}>
              🔒 This chatbot contains confidential HCS documentation
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Admin Login Component
  const AdminLogin = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');

    return (
      <div style={{padding: '2rem', maxWidth: '400px', margin: '0 auto'}}>
        <h2>Admin Login</h2>
        <form onSubmit={(e) => {
          e.preventDefault();
          adminLogin(username, password);
        }}>
          <input
            type="text"
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            style={{width: '100%', padding: '0.5rem', marginBottom: '1rem'}}
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            style={{width: '100%', padding: '0.5rem', marginBottom: '1rem'}}
          />
          <button type="submit" style={{width: '100%', padding: '0.5rem', backgroundColor: '#3b82f6', color: 'white', border: 'none', borderRadius: '0.375rem'}}>
            Login
          </button>
        </form>
        <button onClick={() => setShowAdmin(false)} style={{marginTop: '1rem', color: '#3b82f6'}}>
          Back to Chat
        </button>
      </div>
    );
  };

  // Changelog Modal Component
  const ChangelogModal = () => {
    const currentChangelog = CHANGELOG[CURRENT_VERSION];

    return (
      <div style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        backgroundColor: 'rgba(0, 0, 0, 0.6)',
        backdropFilter: 'blur(4px)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
        padding: '1rem',
        animation: 'fadeIn 0.2s ease-out'
      }}>
        <div style={{
          backgroundColor: 'white',
          borderRadius: '1rem',
          maxWidth: '700px',
          width: '100%',
          maxHeight: '85vh',
          overflow: 'hidden',
          boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
          display: 'flex',
          flexDirection: 'column',
          animation: 'slideUp 0.3s ease-out'
        }}>
          {/* Header */}
          <div style={{
            background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
            padding: '2rem',
            position: 'relative',
            color: 'white'
          }}>
            <button
              onClick={() => setShowChangelog(false)}
              style={{
                position: 'absolute',
                top: '1rem',
                right: '1rem',
                background: 'rgba(255, 255, 255, 0.2)',
                border: 'none',
                borderRadius: '50%',
                width: '32px',
                height: '32px',
                cursor: 'pointer',
                fontSize: '1.25rem',
                color: 'white',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                transition: 'all 0.2s'
              }}
              onMouseEnter={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.3)'}
              onMouseLeave={(e) => e.target.style.background = 'rgba(255, 255, 255, 0.2)'}
              title="Close"
            >
              ×
            </button>

            <div style={{display: 'flex', alignItems: 'center', gap: '1rem'}}>
              <div>
                <h2 style={{
                  margin: 0,
                  fontSize: '1.75rem',
                  fontWeight: '700',
                  marginBottom: '0.25rem'
                }}>
                  {currentChangelog.title}
                </h2>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  fontSize: '0.875rem',
                  opacity: 0.9
                }}>
                  <span style={{
                    background: 'rgba(255, 255, 255, 0.2)',
                    padding: '0.25rem 0.75rem',
                    borderRadius: '1rem',
                    fontWeight: '600'
                  }}>
                    v{CURRENT_VERSION}
                  </span>
                  <span>{currentChangelog.date}</span>
                </div>
              </div>
            </div>
          </div>

          {/* Content */}
          <div style={{
            padding: '2rem',
            overflow: 'auto',
            flex: 1
          }}>
            <h3 style={{
              color: '#1f2937',
              fontSize: '1.125rem',
              fontWeight: '600',
              marginBottom: '1.5rem',
              marginTop: 0
            }}>
              What's New
            </h3>

            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.75rem'
            }}>
              {currentChangelog.features.map((feature, index) => (
                <div key={index} style={{
                  padding: '1rem 1.25rem',
                  background: 'linear-gradient(to right, #f9fafb 0%, #ffffff 100%)',
                  borderRadius: '0.75rem',
                  border: '1px solid #e5e7eb',
                  fontSize: '0.9375rem',
                  lineHeight: '1.6',
                  color: '#374151',
                  transition: 'all 0.2s',
                  cursor: 'default'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = '#3b82f6';
                  e.currentTarget.style.boxShadow = '0 4px 6px -1px rgba(59, 130, 246, 0.1)';
                  e.currentTarget.style.transform = 'translateX(4px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = '#e5e7eb';
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.transform = 'translateX(0)';
                }}>
                  {feature}
                </div>
              ))}
            </div>
          </div>

          {/* Footer */}
          <div style={{
            padding: '1.5rem 2rem',
            borderTop: '1px solid #e5e7eb',
            background: '#f9fafb',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            flexWrap: 'wrap'
          }}>
            <p style={{
              margin: 0,
              fontSize: '0.8125rem',
              color: '#6b7280',
              flex: '1 1 auto'
            }}>
              Access anytime via the What's New button
            </p>
            <button
              onClick={() => {
                localStorage.setItem('lastSeenVersion', CURRENT_VERSION);
                setShowChangelog(false);
              }}
              style={{
                padding: '0.75rem 1.5rem',
                background: 'linear-gradient(135deg, #3b82f6 0%, #2563eb 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '0.5rem',
                cursor: 'pointer',
                fontSize: '0.9375rem',
                fontWeight: '600',
                transition: 'all 0.2s',
                boxShadow: '0 4px 6px -1px rgba(59, 130, 246, 0.3)',
                flex: '0 0 auto'
              }}
              onMouseEnter={(e) => {
                e.target.style.transform = 'translateY(-2px)';
                e.target.style.boxShadow = '0 10px 15px -3px rgba(59, 130, 246, 0.4)';
              }}
              onMouseLeave={(e) => {
                e.target.style.transform = 'translateY(0)';
                e.target.style.boxShadow = '0 4px 6px -1px rgba(59, 130, 246, 0.3)';
              }}
            >
              Got it!
            </button>
          </div>
        </div>

        <style>{`
          @keyframes fadeIn {
            from { opacity: 0; }
            to { opacity: 1; }
          }
          @keyframes slideUp {
            from {
              opacity: 0;
              transform: translateY(20px);
            }
            to {
              opacity: 1;
              transform: translateY(0);
            }
          }
        `}</style>
      </div>
    );
  };

  // Admin Dashboard Component
  const AdminDashboard = () => (
    <div style={{padding: '2rem'}}>
      <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem'}}>
        <h2>Admin Dashboard - User Feedback</h2>
        <div>
          <button onClick={() => loadFeedbackData()} style={{marginRight: '1rem', padding: '0.5rem', backgroundColor: '#10b981', color: 'white', border: 'none', borderRadius: '0.375rem'}}>
            Refresh
          </button>
          <button onClick={() => {setAdminLoggedIn(false); setShowAdmin(false);}} style={{padding: '0.5rem', backgroundColor: '#ef4444', color: 'white', border: 'none', borderRadius: '0.375rem'}}>
            Logout
          </button>
        </div>
      </div>
      
      <p>Total Feedback Entries: <strong>{feedbackData.length}</strong></p>
      
      <div style={{maxHeight: '70vh', overflowY: 'auto'}}>
        {feedbackData.length === 0 ? (
          <p>No feedback entries yet.</p>
        ) : (
          feedbackData.map((feedback) => (
            <div key={feedback.id} style={{border: '1px solid #e5e7eb', borderRadius: '0.5rem', padding: '1rem', marginBottom: '1rem', backgroundColor: '#f9fafb'}}>
              <div style={{display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem'}}>
                <strong>#{feedback.id}</strong>
                <small>{new Date(feedback.timestamp).toLocaleString()}</small>
              </div>
              <p><strong>Query:</strong> {feedback.query}</p>
              <p><strong>Type:</strong> {feedback.feedback_type}</p>
              <p><strong>Description:</strong> {feedback.description}</p>
              <details style={{marginTop: '0.5rem'}}>
                <summary style={{cursor: 'pointer', color: '#6b7280'}}>Response (click to expand)</summary>
                <div style={{backgroundColor: 'white', padding: '0.5rem', marginTop: '0.5rem', borderRadius: '0.25rem', fontSize: '0.875rem'}}>
                  {feedback.response}
                </div>
              </details>
            </div>
          ))
        )}
      </div>
    </div>
  );

  // Show password login if not authenticated
  if (!isAuthenticated) {
    return <PasswordLogin />;
  }

  if (showAdmin) {
    return adminLoggedIn ? <AdminDashboard /> : <AdminLogin />;
  }

  return (
    <div className="container">
      {showChangelog && <ChangelogModal />}

      {showDisclaimer && (
        <div style={{
          position: 'fixed',
          top: 0,
          left: 0,
          right: 0,
          bottom: 0,
          backgroundColor: 'rgba(0, 0, 0, 0.7)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 10000,
          padding: '1rem'
        }}>
          <div style={{
            backgroundColor: 'white',
            borderRadius: '0.5rem',
            padding: '2rem',
            maxWidth: '600px',
            width: '100%',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)'
          }}>
            <h2 style={{
              color: '#1f2937',
              fontSize: '1.5rem',
              fontWeight: '600',
              marginBottom: '1rem'
            }}>
              Welcome to HCSBot
            </h2>
            <div style={{
              color: '#4b5563',
              fontSize: '1rem',
              lineHeight: '1.6',
              marginBottom: '1.5rem'
            }}>
              <p style={{ marginBottom: '1rem' }}>
                HCSBot is an AI-powered assistant that provides information from HCS Technology Group's Apple device management documentation.
              </p>
              <p style={{ marginBottom: '1rem' }}>
                <strong>Please note:</strong>
              </p>
              <ul style={{ paddingLeft: '1.5rem', marginBottom: '1rem' }}>
                <li style={{ marginBottom: '0.5rem' }}>This tool provides information from our documentation library</li>
                <li style={{ marginBottom: '0.5rem' }}>AI responses may occasionally contain errors or inaccuracies</li>
                <li style={{ marginBottom: '0.5rem' }}>Always verify critical information with official documentation</li>
                <li style={{ marginBottom: '0.5rem' }}>For urgent support needs, please contact HCS directly</li>
              </ul>
              <p>
                By clicking "I Understand", you acknowledge these limitations and agree to use this tool as a reference resource.
              </p>
            </div>
            <button
              onClick={acceptDisclaimer}
              style={{
                width: '100%',
                backgroundColor: '#2563eb',
                color: 'white',
                padding: '0.75rem 1.5rem',
                borderRadius: '0.375rem',
                border: 'none',
                fontSize: '1rem',
                fontWeight: '500',
                cursor: 'pointer',
                transition: 'background-color 0.2s'
              }}
              onMouseOver={(e) => e.target.style.backgroundColor = '#1d4ed8'}
              onMouseOut={(e) => e.target.style.backgroundColor = '#2563eb'}
            >
              I Understand
            </button>
          </div>
        </div>
      )}

      {systemStatus !== 'ready' && (
        <div className="status-banner">
          {systemStatus === 'initializing' &&
            'System is initializing... This may take a moment.'}
          {systemStatus === 'error' && (
            <div>
              Unable to connect to the backend server.
              <br />
              <small>
                API endpoint: {API_BASE_URL}
                <br />
                <small style={{fontSize: '11px', opacity: 0.7}}>
                  ENV: {process.env.NODE_ENV} | 
                  API_URL_ENV: {process.env.REACT_APP_API_URL || 'not set'}
                </small>
                {DEBUG_MODE && (
                  <>
                    <br />
                    Debug: Add ?debug=true to URL for console logs
                    <br />
                    User Agent: {navigator.userAgent.includes('Mobile') ? 'Mobile' : 'Desktop'}
                  </>
                )}
              </small>
            </div>
          )}
        </div>
      )}

      <div className="chat-container">
        <div className="chat-header">
          <div className="header-content">
            <img src={`/hcs-logo.png?v=${ASSET_VERSION}`} alt="HCS Logo" className="hcs-logo" />
            <div className="header-text">
              <h1>HCS Technology Group Corby</h1>
              <p>
                Technical professionals. Trusted advisors. Ask me about Apple
                device management, Jamf Pro, iOS deployment, and more.
              </p>
            </div>
            <button
              onClick={() => setShowChangelog(true)}
              style={{
                position: 'absolute',
                top: '1rem',
                right: '1rem',
                backgroundColor: '#3b82f6',
                color: 'white',
                border: 'none',
                padding: '0.5rem 1rem',
                borderRadius: '0.375rem',
                cursor: 'pointer',
                fontSize: '0.875rem',
                fontWeight: '500',
                transition: 'background-color 0.2s'
              }}
              title="See what's new in this version"
              onMouseEnter={(e) => e.target.style.backgroundColor = '#2563eb'}
              onMouseLeave={(e) => e.target.style.backgroundColor = '#3b82f6'}
            >
              What's New
            </button>
          </div>
        </div>

        <div className="chat-messages">
          {messages.map((message, index) => renderMessage(message, index))}

          {isLoading && (
            <div className="message assistant loading">
              <div className="loading-content">
                <span>Thinking</span>
                <div className="loading-dots">
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                  <div className="loading-dot"></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {messages.length === 1 && sampleQuestions.length > 0 && (
          <div className="sample-questions-mobile">
            <button
              className="sample-questions-toggle"
              onClick={() => setShowSampleQuestions(!showSampleQuestions)}
            >
              {showSampleQuestions ? '▼' : '▲'} Try asking about...
            </button>
            {showSampleQuestions && (
              <div className="sample-question-buttons">
                {sampleQuestions.slice(0, 6).map((question, index) => (
                  <button
                    key={index}
                    className="sample-question-button"
                    onClick={() => {
                      handleSampleQuestion(question);
                      setShowSampleQuestions(false);
                    }}
                    disabled={isLoading}
                  >
                    {question}
                  </button>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="chat-input-container">
          <form onSubmit={handleSubmit} className="chat-input-form">
            <textarea
              className="chat-input"
              value={inputText}
              onChange={e => setInputText(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Ask me about Apple device management..."
              disabled={isLoading || systemStatus !== 'ready'}
              rows={1}
            />
            <button
              type="submit"
              className="send-button"
              disabled={
                isLoading || !inputText.trim() || systemStatus !== 'ready'
              }
            >
              ➤
            </button>
          </form>
        </div>
      </div>
    </div>
  );
}

export default App;
