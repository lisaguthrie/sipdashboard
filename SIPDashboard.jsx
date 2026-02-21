import React, { useState, useEffect } from 'react';
import { BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Upload, Search, MessageSquare, X, ChevronDown, ChevronUp, FileText, TrendingUp } from 'lucide-react';

// For external deployments: Set your API key here or use environment variables
// Leave empty for Claude artifacts (authentication handled automatically)
const ANTHROPIC_API_KEY = '';

const SIPDashboard = () => {
  const [schools, setSchools] = useState([]);
  const [selectedSchool, setSelectedSchool] = useState(null);
  const [chatMessages, setChatMessages] = useState([]);
  const [chatInput, setChatInput] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterArea, setFilterArea] = useState('all');
  const [filterLevel, setFilterLevel] = useState('all');
  const [expandedAnalysis, setExpandedAnalysis] = useState(false);
  const [showDataInput, setShowDataInput] = useState(false);
  const [jsonInput, setJsonInput] = useState('');
  const [txtInput, setTxtInput] = useState('');
  const [loading, setLoading] = useState(true);
  const [expandedGoalIndex, setExpandedGoalIndex] = useState(null);
  const [confirmClearChat, setConfirmClearChat] = useState(false);

  // Storage adapter that works in both Claude artifacts and regular browsers
  const storage = {
    get: async (key) => {
      try {
        if (typeof window !== 'undefined' && window.storage && window.storage.get) {
          const result = await window.storage.get(key, true);
          return result?.value || null;
        }
        return localStorage.getItem(key);
      } catch (e) {
        return localStorage.getItem(key);
      }
    },
    set: async (key, value) => {
      try {
        if (typeof window !== 'undefined' && window.storage && window.storage.set) {
          await window.storage.set(key, value, true);
          return;
        }
        localStorage.setItem(key, value);
      } catch (e) {
        localStorage.setItem(key, value);
      }
    },
    remove: async (key) => {
      try {
        if (typeof window !== 'undefined' && window.storage && window.storage.delete) {
          await window.storage.delete(key, true);
          return;
        }
        localStorage.removeItem(key);
      } catch (e) {
        localStorage.removeItem(key);
      }
    }
  };

  const loadData = async () => {
    try {
      const storedData = await storage.get('sip-schools-data');
      if (storedData) {
        const data = JSON.parse(storedData);
        setSchools(data);
        setLoading(false);
      } else {
        setLoading(false);
        setShowDataInput(true);
      }
    } catch (error) {
      console.error('Error loading data:', error);
      setLoading(false);
      setShowDataInput(true);
    }
  };

  const loadTxtData = async () => {
    try {
      const stored = await storage.get('sip-schools-txt');
      if (stored) return stored;
    } catch (error) {
      console.error('Error loading txt data:', error);
    }
    return null;
  };

  const loadChatHistory = async () => {
    try {
      let storedHistory = null;
      if (typeof window !== 'undefined' && window.storage && window.storage.get) {
        const result = await window.storage.get('sip-chat-history', false);
        storedHistory = result?.value || null;
      } else {
        storedHistory = localStorage.getItem('sip-chat-history');
      }
      if (storedHistory) {
        const history = JSON.parse(storedHistory);
        setChatMessages(history);
      }
    } catch (error) {
      console.error('Error loading chat history:', error);
    }
  };

  useEffect(() => {
    loadData();
    loadChatHistory();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const toggleGoal = (index) => {
    setExpandedGoalIndex(expandedGoalIndex === index ? null : index);
  };

  const handleCloseModal = () => {
    setSelectedSchool(null);
    setExpandedGoalIndex(null);
  };

  const saveChatHistory = async (messages) => {
    try {
      if (typeof window !== 'undefined' && window.storage && window.storage.set) {
        await window.storage.set('sip-chat-history', JSON.stringify(messages), false);
      } else {
        localStorage.setItem('sip-chat-history', JSON.stringify(messages));
      }
    } catch (error) {
      console.error('Error saving chat history:', error);
    }
  };

  const handleDataSubmit = async () => {
    try {
      const data = JSON.parse(jsonInput);
      await storage.set('sip-schools-data', JSON.stringify(data));
      if (txtInput.trim()) {
        await storage.set('sip-schools-txt', txtInput.trim());
      }
      setSchools(data);
      setShowDataInput(false);
      setJsonInput('');
      setTxtInput('');
    } catch (error) {
      alert('Invalid JSON. Please check the format and try again.');
    }
  };

  const handleClearData = async () => {
    if (confirm('Are you sure you want to clear all stored data?')) {
      await storage.remove('sip-schools-data');
      await storage.remove('sip-schools-txt');
      setSchools([]);
      setShowDataInput(true);
    }
  };

  const handleExportTable = () => {
    let html = `
<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>School Improvement Plans - ${new Date().toLocaleDateString()}</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    h1 { color: #1e40af; }
    table { border-collapse: collapse; width: 100%; margin-top: 20px; }
    th { background-color: #f3f4f6; padding: 12px; text-align: left; border: 1px solid #d1d5db; font-weight: 600; }
    td { padding: 12px; border: 1px solid #d1d5db; vertical-align: top; }
    tr:hover { background-color: #f9fafb; }
    .badge { display: inline-block; padding: 4px 8px; border-radius: 12px; font-size: 11px; font-weight: 600; margin-bottom: 4px; }
    .badge-ela { background-color: #dbeafe; color: #1e40af; }
    .badge-math { background-color: #d1fae5; color: #065f46; }
    .badge-sel { background-color: #fef3c7; color: #92400e; }
    .badge-other { background-color: #e5e7eb; color: #374151; }
    .badge-grades { background-color: #e9d5ff; color: #6b21a8; }
    .badge-student-group { background-color: #d1fae5; color: #065f46; }
    .school-name { font-weight: 600; }
    .school-level { color: #6b7280; font-size: 14px; }
    .goal-focus { margin-top: 4px; }
    .focus-group { color: #6b7280; font-size: 12px; margin-top: 2px; }
  </style>
</head>
<body>
  <h1>School Improvement Plans</h1>
  <p>Generated: ${new Date().toLocaleString()}</p>
  <p>Total Schools: ${filteredSchools.length}</p>
  <table>
    <thead>
      <tr>
        <th>School</th>
        <th>Goal 1</th>
        <th>Goal 2</th>
        <th>Goal 3</th>
      </tr>
    </thead>
    <tbody>
`;

    filteredSchools.forEach(school => {
      html += `      <tr>
        <td>
          <div class="school-name">${school.name}</div>
          <div class="school-level">${school.level}</div>
        </td>
`;
      school.goals.forEach(goal => {
        const badgeClass = goal.area === 'ELA' ? 'badge-ela' :
                          goal.area === 'Math' ? 'badge-math' :
                          goal.area === 'SEL' ? 'badge-sel' : 'badge-other';
        html += `        <td>
          <span class="badge ${badgeClass}">${goal.area}</span>`;
        if (goal.focus_grades) {
          html += `
          <span class="badge badge-grades">${goal.focus_grades}</span>`;
        }
        if (goal.focus_student_group) {
          html += `
          <span class="badge badge-student-group">${goal.focus_student_group}</span>`;
        }
        html += `
          <div class="goal-focus">${goal.focus_area || goal.focus || 'N/A'}</div>
          <div class="focus-group">${goal.focus_group || ''}</div>
        </td>
`;
      });
      html += `      </tr>
`;
    });

    html += `    </tbody>
  </table>
</body>
</html>`;

    const blob = new Blob([html], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `sip-schools-${new Date().toISOString().split('T')[0]}.html`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // ─── UPDATED: handleChat with system prompt, prompt caching, and conversation history ───
  const handleChat = async () => {
    if (!chatInput.trim() || isProcessing) return;

    const userMessage = chatInput;
    // Build updated message list with the new user message appended
    const newMessages = [...chatMessages, { role: 'user', content: userMessage }];
    setChatMessages(newMessages);
    setChatInput('');
    setIsProcessing(true);

    try {
      const txtContext = await loadTxtData();

      const headers = {
        'Content-Type': 'application/json',
        // anthropic-beta header enables prompt caching
        'anthropic-beta': 'prompt-caching-2024-07-31',
      };

      if (ANTHROPIC_API_KEY) {
        headers['x-api-key'] = ANTHROPIC_API_KEY;
        headers['anthropic-version'] = '2023-06-01';
      }

      // System prompt: attribution rules first, then the (cached) structured text data block
      const systemPrompt = [
        {
          type: 'text',
          text: `You are an expert analyst helping a school board director review School Improvement Plans (SIPs).

CRITICAL ATTRIBUTION RULES — follow these exactly every time:
1. The data is a structured text file where each goal is its own chunk. Every chunk begins with a "School:" line that states the school name. That line is the authoritative source for which school a goal belongs to.
2. When answering questions, always read the "School:" line of each chunk before citing it. Use that school name verbatim.
3. Never transfer information from one school to another. If you are not 100% certain which school a piece of information belongs to, say so explicitly rather than guessing.
4. When listing schools that share a characteristic, verify each school independently by checking its "School:" line before including it in your answer.
5. If you cannot find information for a specific school or goal, say "I could not find that information" rather than substituting data from another school.

RESPONSE STYLE:
- Be concise and accurate.
- When listing multiple schools, use a bulleted list with the school name bolded.
- Always cite the relevant goal area (ELA, Math, SEL, etc.) alongside the school name.`,
        },
        {
          type: 'text',
          // This large block is marked for caching — Anthropic will reuse the
          // processed version across turns as long as the text is identical.
          text: `Here is the complete School Improvement Plan data. It is a structured text file where each goal is represented by a chunk of text. Each chunk begins with a "School:" line identifying the school, followed by the goal number, area, grades, and student group, then the outcome, focus area, current data, strategies, and engagement strategies.\n\n${txtContext || 'No structured text data loaded. Please update data.'}`,
          cache_control: { type: 'ephemeral' },
        },
      ];

      // Convert stored chat messages to the API format.
      // Stored messages use { role, content } which maps directly.
      const apiMessages = newMessages.map(msg => ({
        role: msg.role,
        content: msg.content,
      }));

      const response = await fetch('https://api.anthropic.com/v1/messages', {
        method: 'POST',
        headers,
        body: JSON.stringify({
          model: 'claude-sonnet-4-20250514',
          max_tokens: 1000,
          system: systemPrompt,
          // Full conversation history sent every turn so the model has context
          messages: apiMessages,
        }),
      });

      if (!response.ok) {
        throw new Error(`API error: ${response.status}`);
      }

      const data = await response.json();
      const assistantMessage =
        data.content.find(c => c.type === 'text')?.text || 'Unable to process request.';

      const updatedMessages = [
        ...newMessages,
        { role: 'assistant', content: assistantMessage },
      ];
      setChatMessages(updatedMessages);
      saveChatHistory(updatedMessages);
    } catch (error) {
      console.error('Chat error:', error);
      let errorMsg = 'Sorry, I encountered an error processing your request.';

      if (error.message.includes('Failed to fetch') || error.name === 'TypeError') {
        errorMsg =
          '⚠️ The Anthropic API cannot be called directly from browsers due to CORS restrictions.\n\nTo enable chat, you need a backend proxy server. All other features (tables, charts, search, export) work normally!\n\nContact your developer for setup help.';
      }

      const errorMessages = [
        ...newMessages,
        { role: 'assistant', content: errorMsg },
      ];
      setChatMessages(errorMessages);
      saveChatHistory(errorMessages);
    } finally {
      setIsProcessing(false);
    }
  };
  // ─── END UPDATED handleChat ───

  const stats = {
    total: schools.length,
    goalAreas: schools.reduce((acc, school) => {
      school.goals.forEach(goal => {
        const area = goal.area;
        acc[area] = (acc[area] || 0) + 1;
      });
      return acc;
    }, {}),
    patterns: analyzePatterns(schools)
  };

  function analyzePatterns(schools) {
    if (!schools.length) return [];
    const patterns = [];

    const mlFocus = schools.filter(s =>
      s.goals.some(g => {
        const focusGroup = g.focus_group || '';
        const focusArea = g.focus_area || '';
        const oldFocus = g.focus || '';
        return focusGroup.toLowerCase().includes('multilingual') ||
               focusArea.toLowerCase().includes('multilingual') ||
               oldFocus.toLowerCase().includes('multilingual');
      })
    );
    if (mlFocus.length > 0) {
      patterns.push({
        type: 'theme',
        title: 'Multilingual Learner Focus',
        description: `${mlFocus.length} schools prioritizing ML student support`,
        schools: mlFocus.map(s => s.name)
      });
    }

    const belongingFocus = schools.filter(s =>
      s.goals.some(g => {
        const focusGroup = g.focus_group || '';
        const focusArea = g.focus_area || '';
        const oldFocus = g.focus || '';
        return focusGroup.toLowerCase().includes('belong') ||
               focusArea.toLowerCase().includes('belong') ||
               oldFocus.toLowerCase().includes('belong');
      })
    );
    if (belongingFocus.length > 0) {
      patterns.push({
        type: 'theme',
        title: 'Sense of Belonging',
        description: `${belongingFocus.length} schools focusing on student belonging`,
        schools: belongingFocus.map(s => s.name)
      });
    }

    return patterns;
  }

  const goalAreaData = Object.entries(stats.goalAreas).map(([area, count]) => ({
    area,
    count
  }));

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899'];

  const filteredSchools = schools.filter(school => {
    const matchesSearch = school.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      school.goals.some(g => {
        const focusGroup = g.focus_group || '';
        const focusArea = g.focus_area || '';
        const oldFocus = g.focus || '';
        return focusGroup.toLowerCase().includes(searchTerm.toLowerCase()) ||
               focusArea.toLowerCase().includes(searchTerm.toLowerCase()) ||
               oldFocus.toLowerCase().includes(searchTerm.toLowerCase());
      });
    const matchesFilter = filterArea === 'all' ||
      school.goals.some(g => g.area === filterArea);
    const matchesLevel = filterLevel === 'all' || school.level === filterLevel;
    return matchesSearch && matchesFilter && matchesLevel;
  });

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  if (showDataInput) {
    return (
      <div className="min-h-screen bg-gray-50 p-6">
        <div className="max-w-4xl mx-auto">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <h1 className="text-3xl font-bold mb-4">School Improvement Plan Dashboard</h1>
            <p className="text-gray-600 mb-6">
              Paste your JSON data below to get started. This data will be saved and persist across sessions.
            </p>

            <div className="mb-2 font-medium text-gray-700">JSON Data <span className="text-gray-400 font-normal text-sm">(used for dashboard tables and charts)</span></div>
            <textarea
              value={jsonInput}
              onChange={(e) => setJsonInput(e.target.value)}
              placeholder='Paste your JSON array here (starts with [ and ends with ])'
              className="w-full h-64 p-4 border border-gray-300 rounded-lg font-mono text-sm"
            />

            <div className="mt-4 mb-2 font-medium text-gray-700">Structured Text Data <span className="text-gray-400 font-normal text-sm">(used for AI Q&amp;A)</span></div>
            <textarea
              value={txtInput}
              onChange={(e) => setTxtInput(e.target.value)}
              placeholder='Paste your structured text file here (each goal starts with "School: ...")'
              className="w-full h-64 p-4 border border-gray-300 rounded-lg font-mono text-sm"
            />

            <div className="mt-4 flex gap-4">
              <button
                onClick={handleDataSubmit}
                className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                Load Data
              </button>
              {schools.length > 0 && (
                <button
                  onClick={() => setShowDataInput(false)}
                  className="px-6 py-2 bg-gray-200 rounded-lg hover:bg-gray-300"
                >
                  Cancel
                </button>
              )}
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex justify-between items-start">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">School Improvement Plan Dashboard</h1>
              <p className="text-gray-600">2025-26 School Year • {schools.length} Schools</p>
            </div>
            <div className="flex gap-2">
              <button
                onClick={() => setShowDataInput(true)}
                className="px-4 py-2 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg"
              >
                Update Data
              </button>
              <button
                onClick={handleClearData}
                className="px-4 py-2 text-sm bg-red-50 text-red-600 hover:bg-red-100 rounded-lg"
              >
                Clear Data
              </button>
            </div>
          </div>
        </div>

        {/* Key Stats */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm text-gray-600 mb-1">Total Schools</div>
            <div className="text-3xl font-bold text-blue-600">{schools.length}</div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm text-gray-600 mb-1">Total Goals</div>
            <div className="text-3xl font-bold text-green-600">{schools.length * 3}</div>
          </div>
        </div>

        {/* Focus Group Stats */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm text-gray-600 mb-1">ML Focus</div>
            <div className="text-3xl font-bold text-purple-600">
              {schools.reduce((count, s) =>
                count + s.goals.filter(g => g.focus_student_group === 'ML').length, 0
              )}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm text-gray-600 mb-1">Low Income Focus</div>
            <div className="text-3xl font-bold text-amber-600">
              {schools.reduce((count, s) =>
                count + s.goals.filter(g => g.focus_student_group === 'Low Income').length, 0
              )}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm text-gray-600 mb-1">Special Ed Focus</div>
            <div className="text-3xl font-bold text-rose-600">
              {schools.reduce((count, s) =>
                count + s.goals.filter(g => g.focus_student_group === 'Special Education').length, 0
              )}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm text-gray-600 mb-1">Race/Ethnicity Focus</div>
            <div className="text-3xl font-bold text-indigo-600">
              {schools.reduce((count, s) =>
                count + s.goals.filter(g => g.focus_student_group === 'Race/Ethnicity').length, 0
              )}
            </div>
          </div>
          <div className="bg-white rounded-lg shadow-sm p-6">
            <div className="text-sm text-gray-600 mb-1">All Students Focus</div>
            <div className="text-3xl font-bold text-emerald-600">
              {schools.reduce((count, s) =>
                count + s.goals.filter(g => g.focus_student_group === 'All Students').length, 0
              )}
            </div>
          </div>
        </div>

        {/* Charts */}
        {goalAreaData.length > 0 && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">Goal Areas Distribution</h2>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={goalAreaData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({area, count}) => `${area}: ${count}`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {goalAreaData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>

            <div className="bg-white rounded-lg shadow-sm p-6">
              <h2 className="text-xl font-semibold mb-4">Goals by Area</h2>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={goalAreaData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="area" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="count" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        )}

        {/* Trend Analysis */}
        {stats.patterns.length > 0 && (
          <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div
              className="flex items-center justify-between cursor-pointer"
              onClick={() => setExpandedAnalysis(!expandedAnalysis)}
            >
              <div className="flex items-center gap-2">
                <TrendingUp className="w-5 h-5 text-blue-600" />
                <h2 className="text-xl font-semibold">Trend Analysis & Insights</h2>
              </div>
              {expandedAnalysis ? <ChevronUp /> : <ChevronDown />}
            </div>

            {expandedAnalysis && (
              <div className="mt-4 space-y-4">
                {stats.patterns.map((pattern, idx) => (
                  <div key={idx} className="border-l-4 border-blue-500 pl-4 py-2">
                    <div className="font-semibold text-gray-900">{pattern.title}</div>
                    <div className="text-sm text-gray-600 mb-2">{pattern.description}</div>
                    <div className="text-xs text-gray-500">
                      Schools: {pattern.schools.slice(0, 5).join(', ')}
                      {pattern.schools.length > 5 && ` and ${pattern.schools.length - 5} more`}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {/* Search and Filter */}
        <div className="bg-white rounded-lg shadow-sm p-6 mb-6">
          <div className="flex flex-col gap-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1 relative">
                <Search className="absolute left-3 top-3 w-5 h-5 text-gray-400" />
                <input
                  type="text"
                  placeholder="Search schools or goals..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
              <select
                value={filterLevel}
                onChange={(e) => setFilterLevel(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Schools</option>
                <option value="Elementary School">Elementary Schools</option>
                <option value="Middle School">Middle Schools</option>
                <option value="High School">High Schools</option>
              </select>
              <select
                value={filterArea}
                onChange={(e) => setFilterArea(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="all">All Goal Areas</option>
                <option value="Math">Math</option>
                <option value="ELA">ELA</option>
                <option value="SEL">SEL</option>
                <option value="Other">Other</option>
              </select>
            </div>
            <div className="flex justify-end">
              <button
                onClick={handleExportTable}
                className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 flex items-center gap-2"
              >
                <FileText className="w-4 h-4" />
                Export Table
              </button>
            </div>
          </div>
        </div>

        {/* Schools Table */}
        <div className="bg-white rounded-lg shadow-sm overflow-hidden mb-6">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 border-b">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">School</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Goal 1</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Goal 2</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Goal 3</th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredSchools.map((school, idx) => (
                  <tr key={idx} className="hover:bg-gray-50">
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="font-medium text-gray-900">{school.name}</div>
                      <div className="text-sm text-gray-500">{school.level}</div>
                    </td>
                    {school.goals.map((goal, gIdx) => (
                      <td key={gIdx} className="px-6 py-4">
                        <div className="text-sm">
                          <div className="flex flex-wrap gap-1 mb-2">
                            <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                              {goal.area}
                            </span>
                            {goal.focus_grades && (
                              <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                                {goal.focus_grades}
                              </span>
                            )}
                            {goal.focus_student_group && (
                              <span className="inline-block px-2 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800">
                                {goal.focus_student_group}
                              </span>
                            )}
                          </div>
                          <div className="text-gray-900">
                            {goal.focus_area || goal.focus || 'N/A'}
                          </div>
                          {goal.focus_group && (
                            <div className="text-xs text-gray-500 mt-1 line-clamp-2" title={goal.focus_group}>
                              {goal.focus_group}
                            </div>
                          )}
                        </div>
                      </td>
                    ))}
                    <td className="px-6 py-4 whitespace-nowrap">
                      <button
                        onClick={() => setSelectedSchool(school)}
                        className="text-blue-600 hover:text-blue-800 text-sm font-medium"
                      >
                        View Details
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>

        {/* AI Chat Interface */}
        <div className="bg-white rounded-lg shadow-sm p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-2">
              <MessageSquare className="w-5 h-5 text-blue-600" />
              <h2 className="text-xl font-semibold">Ask Questions About the SIPs</h2>
            </div>
            {chatMessages.length > 0 && (
              confirmClearChat ? (
                <div className="flex items-center gap-2">
                  <span className="text-sm text-gray-600">Clear chat history?</span>
                  <button
                    onClick={async () => {
                      if (typeof window !== 'undefined' && window.storage && window.storage.delete) {
                        await window.storage.delete('sip-chat-history', false);
                      } else {
                        localStorage.removeItem('sip-chat-history');
                      }
                      setChatMessages([]);
                      setConfirmClearChat(false);
                    }}
                    className="text-sm text-white bg-red-500 hover:bg-red-600 px-2 py-1 rounded"
                  >
                    Yes, clear
                  </button>
                  <button
                    onClick={() => setConfirmClearChat(false)}
                    className="text-sm text-gray-500 hover:text-gray-700 px-2 py-1 rounded border"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <button
                  onClick={() => setConfirmClearChat(true)}
                  className="text-sm text-gray-500 hover:text-red-500"
                >
                  Clear Chat
                </button>
              )
            )}
          </div>

          <div className="space-y-4 mb-4 overflow-y-auto resize-y" style={{ minHeight: '500px', maxHeight: '800px', height: '500px' }}>
            {chatMessages.length === 0 && (
              <div className="text-gray-500 text-sm">
                Try asking: "Which schools are focusing on multilingual learners?" or "What are the common SEL themes?"
              </div>
            )}
            {chatMessages.map((msg, idx) => (
              <div key={idx} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
                <div className={`max-w-3xl rounded-lg px-4 py-2 ${
                  msg.role === 'user'
                    ? 'bg-blue-600 text-white'
                    : 'bg-gray-100 text-gray-900'
                }`}>
                  {msg.role === 'user' ? (
                    msg.content
                  ) : (
                    <div className="prose prose-sm max-w-none">
                      {msg.content.split('\n').map((line, i) => {
                        if (line.startsWith('### ')) {
                          return <h3 key={i} className="font-bold text-lg mt-4 mb-2">{line.substring(4)}</h3>;
                        }
                        if (line.startsWith('## ')) {
                          return <h2 key={i} className="font-bold text-xl mt-4 mb-2">{line.substring(3)}</h2>;
                        }
                        if (line.startsWith('# ')) {
                          return <h1 key={i} className="font-bold text-2xl mt-4 mb-2">{line.substring(2)}</h1>;
                        }
                        if (line.startsWith('- ') || line.startsWith('* ')) {
                          return <li key={i} className="ml-4">{line.substring(2)}</li>;
                        }
                        if (line.match(/^\d+\.\s/)) {
                          return <li key={i} className="ml-4">{line.replace(/^\d+\.\s/, '')}</li>;
                        }
                        if (line.includes('**')) {
                          const parts = line.split('**');
                          return (
                            <p key={i} className="mb-2">
                              {parts.map((part, j) =>
                                j % 2 === 1 ? <strong key={j}>{part}</strong> : part
                              )}
                            </p>
                          );
                        }
                        if (line.trim()) {
                          return <p key={i} className="mb-2">{line}</p>;
                        }
                        return <br key={i} />;
                      })}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {isProcessing && (
              <div className="flex justify-start">
                <div className="bg-gray-100 rounded-lg px-4 py-2 text-gray-900">
                  <div className="animate-pulse">Analyzing SIP data...</div>
                </div>
              </div>
            )}
          </div>

          <div className="flex gap-2">
            <input
              type="text"
              value={chatInput}
              onChange={(e) => setChatInput(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleChat()}
              placeholder="Ask a question about the School Improvement Plans..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={isProcessing}
            />
            <button
              onClick={handleChat}
              disabled={isProcessing || !chatInput.trim()}
              className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
            >
              Ask
            </button>
          </div>
        </div>

        {/* School Detail Modal */}
        {selectedSchool && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="sticky top-0 bg-white border-b p-6 flex justify-between items-start z-10">
                <div>
                  <h2 className="text-2xl font-bold text-gray-900">{selectedSchool.name}</h2>
                  <p className="text-gray-600">{selectedSchool.level}</p>
                </div>
                <button
                  onClick={handleCloseModal}
                  className="text-gray-400 hover:text-gray-600"
                >
                  <X className="w-6 h-6" />
                </button>
              </div>

              <div className="p-6 space-y-6 overflow-y-auto">
                <div>
                  <h3 className="text-lg font-semibold mb-4">School Improvement Goals</h3>
                  <div className="space-y-3">
                    {selectedSchool.goals.map((goal, idx) => (
                      <div key={idx} className="border border-gray-200 rounded-lg overflow-hidden">
                        <div
                          className="flex items-center justify-between p-4 bg-gray-50 cursor-pointer hover:bg-gray-100 transition-colors"
                          onClick={() => toggleGoal(idx)}
                        >
                          <div className="flex-1">
                            <div className="flex items-center gap-2 mb-2 flex-wrap">
                              <span className="text-sm font-medium text-gray-900">Goal {idx + 1}</span>
                              <span className="px-2 py-1 text-xs font-semibold rounded-full bg-blue-100 text-blue-800">
                                {goal.area}
                              </span>
                              {goal.focus_grades && (
                                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-purple-100 text-purple-800">
                                  {goal.focus_grades}
                                </span>
                              )}
                              {goal.focus_student_group && (
                                <span className="px-2 py-1 text-xs font-semibold rounded-full bg-emerald-100 text-emerald-800">
                                  {goal.focus_student_group}
                                </span>
                              )}
                            </div>
                            {goal.focus_area && (
                              <div className="text-sm text-gray-900 font-medium">
                                {goal.focus_area}
                              </div>
                            )}
                            {goal.focus && !goal.focus_area && (
                              <div className="text-sm text-gray-900 font-medium">
                                {goal.focus}
                              </div>
                            )}
                          </div>
                          <div className="ml-4">
                            {expandedGoalIndex === idx ? (
                              <ChevronUp className="w-5 h-5 text-gray-500" />
                            ) : (
                              <ChevronDown className="w-5 h-5 text-gray-500" />
                            )}
                          </div>
                        </div>

                        {expandedGoalIndex === idx && (
                          <div className="p-4 bg-white border-t border-gray-200">
                            <div className="text-sm text-gray-600 mb-3">
                              <span className="font-semibold text-gray-700">Outcome:</span> {goal.outcome}
                            </div>
                            {goal.strategies_summarized && (
                              <div>
                                <div className="text-sm font-semibold text-gray-700 mb-2">Strategies:</div>
                                <div className="text-sm text-gray-700 leading-relaxed">
                                  {goal.strategies_summarized}
                                </div>
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default SIPDashboard;
