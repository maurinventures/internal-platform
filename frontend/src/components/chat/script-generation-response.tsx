import { AssetClipCard } from "../script/asset-clip-card";
import { AISegmentCard } from "../script/ai-segment-card";
import { TimelineOverview } from "../script/timeline-overview";
import { ExportOptions } from "../script/export-options";

export interface ScriptSegment {
  type: "asset" | "ai";
  // Asset clip fields
  assetType?: "video" | "audio";
  sourceFile?: string;
  startTime?: string;
  endTime?: string;
  transcript?: string;
  visualAnalysis?: string; // AI analysis of what's happening visually in the video
  clipNumber?: number;
  // AI segment fields
  content?: string;
  segmentNumber?: number;
  reason?: string;
  // Common
  duration: string;
}

export interface ScriptGenerationData {
  description: string;
  segments: ScriptSegment[];
  totalDuration: string;
  clipCount: number;
  aiSegmentCount: number;
}

interface ScriptGenerationResponseProps {
  data: ScriptGenerationData;
}

export function ScriptGenerationResponse({ data }: ScriptGenerationResponseProps) {
  // Build timeline segments for the overview
  const timelineSegments = data.segments.map((segment, index) => {
    // Calculate start time based on previous segments
    let startTime = 0;
    for (let i = 0; i < index; i++) {
      const prevDuration = data.segments[i].duration;
      // Convert duration string like "0:08" to seconds
      const [mins, secs] = prevDuration.split(':').map(Number);
      startTime += (mins * 60) + secs;
    }
    
    // Convert current duration to seconds
    const [mins, secs] = segment.duration.split(':').map(Number);
    const duration = (mins * 60) + secs;
    
    return {
      type: segment.type === "asset" ? "clip" as const : "ai" as const,
      startTime,
      duration,
      label: segment.type === "asset" 
        ? `Clip ${segment.clipNumber}` 
        : `AI Segment ${segment.segmentNumber}`
    };
  });

  // Convert total duration to seconds
  const [totalMins, totalSecs] = data.totalDuration.split(':').map(Number);
  const totalDurationSeconds = (totalMins * 60) + totalSecs;

  return (
    <div className="space-y-4 mt-2">
      {/* Header */}
      <div>
        <h3 className="font-semibold text-[14px] mb-1">Video Script Generated</h3>
        <p className="text-muted-foreground text-[12px] mb-3">
          {data.description}
        </p>
        <ExportOptions />
      </div>

      {/* Script Breakdown */}
      <div className="space-y-3">
        <h4 className="font-medium text-[12px]">Script Breakdown</h4>
        
        {data.segments.map((segment, index) => (
          <div key={index}>
            {segment.type === "asset" ? (
              <AssetClipCard
                type={segment.assetType!}
                sourceFile={segment.sourceFile!}
                startTime={segment.startTime!}
                endTime={segment.endTime!}
                duration={segment.duration}
                transcript={segment.transcript!}
                visualAnalysis={segment.visualAnalysis!}
                clipNumber={segment.clipNumber!}
              />
            ) : (
              <AISegmentCard
                content={segment.content!}
                duration={segment.duration}
                segmentNumber={segment.segmentNumber!}
                reason={segment.reason!}
              />
            )}
          </div>
        ))}
      </div>
    </div>
  );
}