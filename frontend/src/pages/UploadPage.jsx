import { useState, useRef, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { UploadCloud, File as FileIcon, X, KeyRound, HelpCircle, ArrowRight } from "lucide-react";
import ApiKeyDocsModal from "../components/ApiKeyDocsModal";

export default function UploadPage() {
  const [files, setFiles] = useState([]);
  const [isUploading, setIsUploading] = useState(false);
  const [apiKey, setApiKey] = useState("");
  const [apiProvider, setApiProvider] = useState("groq");
  const [isDocsModalOpen, setIsDocsModalOpen] = useState(false);
  
  const fileInputRef = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const savedKey = localStorage.getItem("pdfx_api_key");
    const savedProvider = localStorage.getItem("pdfx_api_provider");
    if (savedKey) setApiKey(savedKey);
    if (savedProvider) setApiProvider(savedProvider);
  }, []);

  const handleKeyChange = (e) => {
    const val = e.target.value;
    setApiKey(val);
    localStorage.setItem("pdfx_api_key", val);
  };

  const handleProviderChange = (e) => {
    const val = e.target.value;
    setApiProvider(val);
    localStorage.setItem("pdfx_api_provider", val);
  };

  const handleFileChange = (e) => {
    if (e.target.files) {
      setFiles([...files, ...Array.from(e.target.files)]);
    }
  };

  const removeFile = (index) => {
    setFiles(files.filter((_, i) => i !== index));
  };

  const handleUpload = async () => {
    if (files.length === 0) {
      alert("Please upload at least one PDF.");
      return;
    }
    if (!apiKey.trim()) {
      alert("An API key is required to process the documents.");
      return;
    }
    
    setIsUploading(true);
    const formData = new FormData();
    files.forEach(file => formData.append("files", file));
    formData.append("api_key", apiKey.trim());
    formData.append("api_provider", apiProvider);

    try {
      const res = await fetch("http://localhost:8000/api/jobs", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (res.ok) {
        navigate(`/job/${data.job_id}/progress`);
      } else {
        alert("Upload failed: " + (data.detail || "Unknown error"));
      }
    } catch (err) {
      alert("Upload failed. Make sure backend is running.");
    } finally {
      setIsUploading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto animate-in fade-in duration-700 pb-20 pt-2">
      
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-12 items-start">
        
        {/* Left Column: Hero & Information */}
        <div className="lg:col-span-5 space-y-10 lg:sticky lg:top-28">
          <div className="space-y-6">
            {/* Parchment Colored Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1.5 rounded-full bg-[#f5ebd9] border border-[#e6d5b8] text-[#5c4a3d] font-bold text-[11px] tracking-widest uppercase shadow-sm">
              Bring Your Own Key
            </div>
            <h1 className="text-5xl md:text-6xl font-bold tracking-tight text-stone-900 font-serif leading-[1.1]">
              Curate your question bank.
            </h1>
          </div>

          <div className="space-y-5 mt-12 lg:mt-24">
            <h3 className="text-sm font-bold text-stone-800 uppercase tracking-widest border-b-2 border-stone-200 pb-3">How it works</h3>
            <div className="space-y-4">
              {/* Unified Espresso Steps */}
              <StepRow 
                number="1" 
                title="Upload" 
                desc="Provide your scanned PDFs." 
                colorClass="bg-stone-800 text-white"
              />
              <StepRow 
                number="2" 
                title="Authenticate" 
                desc="Supply your API key." 
                colorClass="bg-stone-800 text-white"
              />
              <StepRow 
                number="3" 
                title="Review" 
                desc="Obtain a structured document." 
                colorClass="bg-stone-800 text-white"
              />
            </div>
          </div>
        </div>

        {/* Right Column: Interaction Area */}
        <div className="lg:col-span-7 space-y-6">
          
          {/* Upload Card */}
          <div className="bg-white rounded-2xl border border-stone-200 p-6 md:p-8 shadow-sm transition-all hover:shadow-md flex flex-col">
            <div 
              className="border-2 border-dashed border-stone-300 rounded-xl p-10 text-center hover:bg-rose-50/50 hover:border-rose-900/30 transition-all cursor-pointer group flex-1 flex flex-col items-center justify-center min-h-[250px]"
              onClick={() => fileInputRef.current?.click()}
            >
              <input 
                type="file" 
                multiple 
                accept="application/pdf" 
                className="hidden" 
                ref={fileInputRef}
                onChange={handleFileChange}
              />
              <div className="mx-auto w-16 h-16 bg-stone-100 rounded-full flex items-center justify-center mb-5 group-hover:bg-rose-100 transition-colors">
                <UploadCloud className="w-8 h-8 text-stone-600 group-hover:text-rose-900 transition-colors" />
              </div>
              <h3 className="text-xl font-serif font-medium mb-2 text-stone-900 group-hover:text-rose-900 transition-colors">Upload Documents</h3>
              <p className="text-stone-500 text-sm group-hover:text-rose-900/70 transition-colors">Click here or drag your PDFs into this box</p>
            </div>

            {files.length > 0 && (
              <div className="mt-8 space-y-4 animate-in fade-in">
                <div className="flex justify-between items-end border-b border-stone-100 pb-2">
                  <h4 className="font-medium text-stone-800 text-sm">Selected Files</h4>
                  <span className="text-xs text-stone-500">{files.length} file(s)</span>
                </div>
                
                <div className="grid grid-cols-1 gap-2 max-h-48 overflow-y-auto pr-2 custom-scrollbar">
                  {files.map((f, i) => (
                    <div key={i} className="flex items-center gap-3 bg-stone-50 px-4 py-3 rounded-lg border border-stone-200 group">
                      <FileIcon className="w-4 h-4 text-stone-500" />
                      <span className="flex-1 truncate text-sm text-stone-700 font-medium">{f.name}</span>
                      <button 
                        onClick={() => removeFile(i)}
                        className="p-1.5 text-stone-400 hover:text-red-500 transition-colors opacity-0 group-hover:opacity-100"
                      >
                        <X className="w-4 h-4" />
                      </button>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* API Setup Card */}
          <div className="bg-white rounded-2xl border border-stone-200 p-6 md:p-8 shadow-sm transition-all hover:shadow-md">
            <div className="flex items-center justify-between mb-6">
              <h3 className="text-xl font-semibold text-stone-900 flex items-center gap-2 font-serif">
                <KeyRound className="w-5 h-5 text-stone-400" />
                API Configuration
              </h3>
              <button 
                onClick={() => setIsDocsModalOpen(true)}
                className="flex items-center gap-1.5 text-xs font-medium text-stone-500 hover:text-stone-900 transition-colors bg-stone-100 px-3 py-1.5 rounded-lg"
              >
                <HelpCircle className="w-3.5 h-3.5" />
                How to get a key
              </button>
            </div>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">Provider</label>
                <select 
                  value={apiProvider}
                  onChange={handleProviderChange}
                  className="w-full bg-stone-50 border border-stone-200 text-stone-800 text-sm rounded-lg focus:ring-1 focus:ring-rose-900 focus:border-rose-900 block p-3 outline-none transition-all appearance-none"
                >
                  <option value="groq">Groq (Recommended)</option>
                  <option value="gemini">Google Gemini</option>
                  <option value="openai">OpenAI</option>
                  <option value="claude">Claude</option>
                </select>
              </div>

              <div>
                <label className="block text-xs font-semibold text-stone-500 uppercase tracking-wider mb-2">API Key</label>
                <input 
                  type="password" 
                  placeholder="Paste your key here"
                  value={apiKey}
                  onChange={handleKeyChange}
                  className="w-full bg-stone-50 border border-stone-200 text-stone-800 text-sm rounded-lg focus:ring-1 focus:ring-rose-900 focus:border-rose-900 block p-3 outline-none transition-all placeholder:text-stone-400"
                />
              </div>
            </div>
          </div>

          {/* Master Submit Button (Burgundy) */}
          <button
            onClick={handleUpload}
            disabled={isUploading || !apiKey || files.length === 0}
            className={`w-full font-medium py-4 rounded-xl shadow-sm transition-all flex items-center justify-center gap-3 text-lg mt-4
              ${(isUploading || !apiKey || files.length === 0) 
                ? 'bg-stone-300 cursor-not-allowed text-stone-500' 
                : 'bg-rose-900 hover:bg-rose-950 text-white active:scale-[0.99] shadow-rose-900/20 hover:shadow-lg hover:shadow-rose-900/30'}`}
          >
            {isUploading ? (
              <>
                <div className="w-5 h-5 border-2 border-rose-400 border-t-white rounded-full animate-spin" />
                Processing...
              </>
            ) : (
              <>
                Start Processing
                <ArrowRight className="w-5 h-5" />
              </>
            )}
          </button>

        </div>
      </div>

      <ApiKeyDocsModal isOpen={isDocsModalOpen} onClose={() => setIsDocsModalOpen(false)} />
    </div>
  );
}

function StepRow({ number, title, desc, colorClass }) {
  return (
    <div className="flex items-center gap-5 p-4 rounded-xl bg-white border border-stone-200 shadow-sm hover:shadow-md transition-all group">
      <div className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg shrink-0 transition-all shadow-inner group-hover:scale-105 ${colorClass}`}>
        {number}
      </div>
      <div>
        <h4 className="text-stone-900 font-serif font-bold text-lg mb-0.5">{title}</h4>
        <p className="text-stone-600 text-sm leading-relaxed">{desc}</p>
      </div>
    </div>
  );
}
