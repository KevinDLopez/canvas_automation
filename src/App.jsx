import React from "react";

export default function App() {
  const handleClick = () => {
    alert("Button was clicked!");
  };

  return (
    <div className="min-h-screen max-h-full bg-zinc-950">
      <div className="font-bold text-white">
        Testing 2
        <button 
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded" 
          onClick={handleClick}
        >
          Click Me
        </button>

        <button 
          className="mt-4 px-4 py-2 bg-blue-500 text-white rounded" 
          onClick={handleClick}
        >
          Click Me
        </button>
      </div>
    </div>
  );
}