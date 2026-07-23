import { Card } from '@/components/UI/Card';
import { Stat } from '@/components/UI/Stat';

export const MissionsPage = () => {
  return (
    <div className="py-8">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <h1 className="mb-6 text-2xl font-bold text-text-primary">My Missions</h1>
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          <Stat title="Active Missions" value="5" trend="up" />
          <Stat title="Completed This Week" value="12" trend="up" />
          <Stat title="Success Rate" value="78%" trend="up" />
        </div>

        <div className="mt-8">
          <h2 className="mb-4 text-xl font-semibold text-text-primary">Active Missions</h2>
          <div className="space-y-4">
            <MissionItem
              title="Acquire undervalued electronics lot"
              description="Seek underpriced pallets of consumer electronics for resale"
              progress={65}
              deadline="2024-01-15"
            />
            <MissionItem
              title="Build vintage watch collection"
              description="Acquire 5 rare timepieces under $500 each"
              progress={40}
              deadline="2024-03-01"
            />
            <MissionItem
              title="Flip designer furniture"
              description="Find mid-century modern pieces needing light restoration"
              progress={30}
              deadline="2024-02-28"
            />
          </div>
        </div>
      </div>
    </div>
  );
};

const MissionItem = ({ title, description, progress, deadline }: {
  title: string;
  description: string;
  progress: number; // 0-100
  deadline: string;
}) => (
  <Card>
    <div className="space-y-4">
      <div className="flex justify-between items-start">
        <h3 className="font-semibold text-text-primary">{title}</h3>
        <span className="text-xs text-text-secondary">{deadline}</span>
      </div>
      <p className="text-text-secondary/80">{description}</p>
      <div className="flex items-center space-x-3">
        <div className="flex-1">
          <div className="w-full bg-border/50 rounded-full h-2.5">
            <div className={`h-2.5 bg-accent rounded-full transition-all width-[${progress}%]`}></div>
          </div>
        </div>
        <span className="text-xs text-text-secondary">{progress}%</span>
      </div>
    </div>
  );
};

// Reuse Card from earlier