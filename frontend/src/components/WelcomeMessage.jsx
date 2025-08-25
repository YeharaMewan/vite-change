export default function WelcomeMessage() {
  return (
    <div className="flex flex-col bg-gray-900 items-center justify-center h-full px-4 py-8">
      <div className="text-center max-w-4xl">
        <h1 className="text-4xl font-semibold text-white mb-8">
          What can I help with?
        </h1>
        
        {/* Sample prompts */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 w-full max-w-3xl">
          <button className="p-4 bg-gray-800 hover:bg-gray-700 rounded-2xl text-left transition-all duration-200 shadow-sm">
            <div className="text-white font-medium mb-1">HR Policy Questions</div>
            <div className="text-white/70 text-sm">Get information about company policies and procedures</div>
          </button>
          
          <button className="p-4 bg-gray-800 hover:bg-gray-700 rounded-2xl text-left transition-all duration-200 shadow-sm">
            <div className="text-white font-medium mb-1">Employee Benefits</div>
            <div className="text-white/70 text-sm">Learn about health insurance, retirement plans, and perks</div>
          </button>
          
          <button className="p-4 bg-gray-800 hover:bg-gray-700 rounded-2xl text-left transition-all duration-200 shadow-sm">
            <div className="text-white font-medium mb-1">Leave Management</div>
            <div className="text-white/70 text-sm">Submit leave requests and check balances</div>
          </button>
          
          <button className="p-4 bg-gray-800 hover:bg-gray-700 rounded-2xl text-left transition-all duration-200 shadow-sm">
            <div className="text-white font-medium mb-1">Performance Reviews</div>
            <div className="text-white/70 text-sm">Get help with performance evaluations and feedback</div>
          </button>
        </div>
      </div>
    </div>
  );
}