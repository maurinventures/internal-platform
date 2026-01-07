interface TimelineSegment {
  type: "clip" | "ai";
  startTime: number;
  duration: number;
  label: string;
}

interface TimelineOverviewProps {
  segments: TimelineSegment[];
  totalDuration: number;
}

export function TimelineOverview({ segments, totalDuration }: TimelineOverviewProps) {
  return (
    <div className="border border-border rounded-lg p-4 bg-card">
      <div className="space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-medium">Timeline Overview</h3>
          <span className="text-sm text-muted-foreground">
            Total: {Math.floor(totalDuration / 60)}:{(totalDuration % 60).toString().padStart(2, "0")}
          </span>
        </div>

        {/* Timeline Bar */}
        <div className="relative h-12 bg-muted rounded overflow-hidden">
          {segments.map((segment, index) => {
            const leftPercent = (segment.startTime / totalDuration) * 100;
            const widthPercent = (segment.duration / totalDuration) * 100;

            return (
              <div
                key={index}
                className={`absolute h-full ${
                  segment.type === "clip" ? "bg-primary" : "bg-primary/40"
                } border-r border-background/20 hover:opacity-80 transition-opacity cursor-pointer group`}
                style={{
                  left: `${leftPercent}%`,
                  width: `${widthPercent}%`,
                }}
                title={segment.label}
              >
                <div className="absolute inset-0 flex items-center justify-center">
                  <span className="text-xs text-white font-medium opacity-0 group-hover:opacity-100 transition-opacity">
                    {segment.label}
                  </span>
                </div>
              </div>
            );
          })}
        </div>

        {/* Legend */}
        <div className="flex items-center gap-4 text-xs">
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-primary"></div>
            <span className="text-muted-foreground">Asset Clips</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-4 h-4 rounded bg-primary/40"></div>
            <span className="text-muted-foreground">AI Generated</span>
          </div>
        </div>
      </div>
    </div>
  );
}
