import { X, ExternalLink, KeyRound, BookOpen } from "lucide-react";

export default function ApiKeyDocsModal({ isOpen, onClose }) {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-stone-900/40 backdrop-blur-sm animate-in fade-in duration-200">
      <div 
        className="bg-stone-50 rounded-xl border border-stone-200 max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="sticky top-0 bg-stone-50/90 backdrop-blur z-10 border-b border-stone-200 p-6 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-stone-200/50 p-2 rounded-lg text-stone-700">
              <KeyRound className="w-5 h-5" />
            </div>
            <h2 className="text-xl font-bold font-serif text-stone-900">Understanding API Keys</h2>
          </div>
          <button 
            onClick={onClose}
            className="p-2 text-stone-400 hover:text-stone-800 hover:bg-stone-200/50 rounded-lg transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Content */}
        <div className="p-6 space-y-8">
          
          {/* Simple Explanation */}
          <section className="bg-white rounded-xl p-6 border border-stone-200 shadow-sm">
            <h3 className="text-lg font-serif font-semibold text-stone-900 mb-3">
              Your Access Pass
            </h3>
            <p className="text-stone-600 leading-relaxed text-sm">
              Think of an API Key as a <strong>library card</strong>. Our platform operates entirely on your local machine, but to read and process your examination papers, we must interface with large artificial intelligence models (such as Google Gemini, Groq, or OpenAI). 
              <br /><br />
              These institutions distribute "keys" allowing you to use their models. You simply obtain a key from their respective websites, provide it here, and we handle the complex processing. Many providers offer generous free tiers.
            </p>
          </section>

          {/* How to get it */}
          <section className="space-y-4">
            <h3 className="text-lg font-serif font-semibold text-stone-900 flex items-center gap-2 border-b border-stone-200 pb-2">
              <BookOpen className="w-4 h-4 text-stone-500" />
              Acquiring an API Key
            </h3>
            
            <div className="space-y-4 pt-2">
              
              {/* Groq */}
              <div className="bg-white rounded-xl p-6 border border-stone-200 shadow-sm hover:border-stone-300 transition-colors">
                <div className="flex justify-between items-start mb-4">
                  <h4 className="text-base font-serif font-semibold text-stone-900">Groq (Recommended)</h4>
                  <a 
                    href="https://console.groq.com/keys" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-sm text-stone-600 hover:text-stone-900 font-medium bg-stone-100 px-3 py-1.5 rounded-md transition-colors"
                  >
                    Obtain Groq Key <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
                <ol className="list-decimal list-inside text-stone-600 space-y-2 text-sm leading-relaxed">
                  <li>Navigate to the Groq Console using the link above.</li>
                  <li>Authenticate using your Google account.</li>
                  <li>Select <strong>"Create API Key"</strong>.</li>
                  <li>Copy the provided string (beginning with <code className="bg-stone-100 px-1.5 py-0.5 rounded text-stone-800 border border-stone-200 font-mono text-xs">gsk_...</code>) and provide it on our platform.</li>
                </ol>
              </div>

              {/* Google Gemini */}
              <div className="bg-white rounded-xl p-6 border border-stone-200 shadow-sm hover:border-stone-300 transition-colors">
                <div className="flex justify-between items-start mb-4">
                  <h4 className="text-base font-serif font-semibold text-stone-900">Google Gemini</h4>
                  <a 
                    href="https://aistudio.google.com/app/apikey" 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center gap-1.5 text-sm text-stone-600 hover:text-stone-900 font-medium bg-stone-100 px-3 py-1.5 rounded-md transition-colors"
                  >
                    Obtain Gemini Key <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </div>
                <ol className="list-decimal list-inside text-stone-600 space-y-2 text-sm leading-relaxed">
                  <li>Navigate to Google AI Studio.</li>
                  <li>Authenticate using your Google account.</li>
                  <li>Select <strong>"Create API Key"</strong> within a new project.</li>
                  <li>Copy the resulting key and provide it here.</li>
                </ol>
              </div>

            </div>
          </section>

          <div className="bg-stone-200/50 p-4 rounded-lg text-xs text-stone-500 text-center font-medium">
            Note: Your API key is stored locally within your browser for convenience. We do not transmit it to our servers.
          </div>

        </div>
      </div>
    </div>
  );
}
