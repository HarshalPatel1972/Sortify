import { useState, useEffect } from "react";
import { Outlet, Link } from "react-router-dom";
import { BookOpen, Star } from "lucide-react";

const FRAMES = [
  "Sortify",
  "oSrstify".replace('s', ''), // wait, let's just write them directly
  "oSrtify",
  "orStify",
  "orSitfy",
  "orSifty",
  "oriSfty",
  "orifSty",
  "oirfSty",
  "oifrSty",
  "iofrSty",
  "iforSty",
  "fiorSty"
];

function AnimatedLogo() {
  const [text, setText] = useState("Sortify");

  useEffect(() => {
    let frameIndex = 0;
    let isReversing = false;

    // Wait 1 second before starting the sort
    const startDelay = setTimeout(() => {
      const interval = setInterval(() => {
        if (!isReversing) {
          frameIndex++;
          if (frameIndex >= FRAMES.length) {
            // Reached the sorted state
            frameIndex = FRAMES.length - 1;
            isReversing = true; // start going back
            // Pause at the sorted state for 1 second before reversing
            clearInterval(interval);
            setTimeout(() => {
              const reverseInterval = setInterval(() => {
                frameIndex--;
                if (frameIndex < 0) {
                  frameIndex = 0;
                  clearInterval(reverseInterval); // Finished returning to original
                  setText(FRAMES[0]);
                } else {
                  setText(FRAMES[frameIndex]);
                }
              }, 150); // fast reverse
            }, 1000);
          } else {
            setText(FRAMES[frameIndex]);
          }
        }
      }, 300); // Slow sorting (300ms per swap)
      
      return () => clearInterval(interval);
    }, 1000);

    return () => clearTimeout(startDelay);
  }, []);

  return (
    <span className="inline-block min-w-[80px] cursor-default font-mono tracking-wider text-stone-900">
      {text}
    </span>
  );
}

export default function Layout() {
  return (
    <div className="min-h-screen bg-stone-50 text-stone-800 font-sans selection:bg-stone-200">
      <header className="border-b border-stone-200 bg-stone-50/80 backdrop-blur-md sticky top-0 z-50">
        <div className="max-w-6xl mx-auto px-6 h-20 flex items-center justify-between">
          <div className="flex items-center gap-3 font-serif font-bold text-2xl tracking-tight text-stone-900">
            <BookOpen className="w-7 h-7 text-stone-700" />
            <AnimatedLogo />
          </div>
          
          <a 
            href="https://github.com/HarshalPatel1972/Sortify.git" 
            target="_blank" 
            rel="noopener noreferrer"
            className="flex items-center gap-2 px-4 py-2 rounded-lg bg-stone-100 hover:bg-stone-200 text-stone-700 font-medium text-sm transition-colors border border-stone-200 group"
          >
            <Star className="w-4 h-4 text-amber-500 group-hover:scale-110 transition-transform" />
            Star on GitHub
          </a>
        </div>
      </header>
      
      <main className="max-w-6xl mx-auto px-6 pb-12 pt-4">
        <Outlet />
      </main>
    </div>
  );
}
