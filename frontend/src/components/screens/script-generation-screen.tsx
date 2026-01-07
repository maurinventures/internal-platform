import { useState } from "react";
import { Sidebar } from "../chat/sidebar";
import { ModelSelector } from "../chat/model-selector";
import { ChatMessage } from "../chat/chat-message";
import { AssetClipCard } from "../script/asset-clip-card";
import { AISegmentCard } from "../script/ai-segment-card";
import { TimelineOverview } from "../script/timeline-overview";
import { ExportOptions } from "../script/export-options";
import { CommandPalette } from "../command-palette";
import { ScrollArea } from "../ui/scroll-area";
import { Button } from "../ui/button";
import { ArrowLeft } from "lucide-react";

export function ScriptGenerationScreen() {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [model] = useState("claude-3-sonnet");

  const handleNewChat = () => {
    console.log("New chat");
  };

  // Mock timeline data
  const timelineSegments = [
    { type: "clip" as const, startTime: 0, duration: 8, label: "Clip 1" },
    { type: "ai" as const, startTime: 8, duration: 5, label: "AI Segment 1" },
    { type: "clip" as const, startTime: 13, duration: 12, label: "Clip 2" },
    { type: "clip" as const, startTime: 25, duration: 7, label: "Clip 3" },
    { type: "ai" as const, startTime: 32, duration: 4, label: "AI Segment 2" },
    { type: "clip" as const, startTime: 36, duration: 9, label: "Clip 4" },
  ];

  return (
    <div className="flex h-screen bg-background overflow-hidden">
      <CommandPalette />
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggleCollapse={() => setSidebarCollapsed(!sidebarCollapsed)}
        onNewChat={handleNewChat}
      />

      <div className="flex-1 flex flex-col min-w-0">
        <ModelSelector value={model} onChange={() => {}} />

        <ScrollArea className="flex-1">
          <div className="max-w-4xl mx-auto p-6 space-y-6">
            {/* Back Button */}
            <Button variant="ghost" size="sm">
              <ArrowLeft className="mr-2 h-4 w-4" />
              Back to Chat
            </Button>

            {/* User Query */}
            <ChatMessage
              role="user"
              content="Create a 60-second video script about our new AI product launch, using clips from my library that highlight innovation and customer testimonials."
              timestamp="2:34 PM"
            />

            {/* AI Response Header */}
            <div className="space-y-4">
              <div className="flex items-start justify-between">
                <div>
                  <h2 className="text-xl font-semibold mb-2">Video Script Generated</h2>
                  <p className="text-muted-foreground">
                    I've created a 60-second video script using 4 clips from your library and 2 AI-generated segments to fill gaps.
                  </p>
                </div>
                <ExportOptions />
              </div>

              {/* Timeline Overview */}
              <TimelineOverview segments={timelineSegments} totalDuration={45} />
            </div>

            {/* Script Segments */}
            <div className="space-y-4">
              <h3 className="font-semibold">Script Breakdown</h3>

              <AssetClipCard
                type="video"
                sourceFile="product_demo_final.mp4"
                startTime="0:15"
                endTime="0:23"
                duration="0:08"
                transcript="Welcome to the future of AI-powered solutions. Our new product revolutionizes how businesses interact with their customers."
                clipNumber={1}
              />

              <AISegmentCard
                content="[Transition] This innovation didn't happen overnight. It's the result of years of research and development."
                duration="0:05"
                segmentNumber={1}
                reason="Connecting product intro to customer testimonials"
              />

              <AssetClipCard
                type="video"
                sourceFile="customer_testimonial_sarah.mp4"
                startTime="1:42"
                endTime="1:54"
                duration="0:12"
                transcript="Since implementing this solution, we've seen a 300% increase in customer engagement. It's been absolutely transformative for our business."
                clipNumber={2}
              />

              <AssetClipCard
                type="audio"
                sourceFile="interview_cto_insights.mp3"
                startTime="3:20"
                endTime="3:27"
                duration="0:07"
                transcript="The technology behind this is cutting-edge. We've built it on a foundation of machine learning and natural language processing."
                clipNumber={3}
              />

              <AISegmentCard
                content="[Call to Action] Ready to transform your business? Join thousands of companies already using our platform."
                duration="0:04"
                segmentNumber={2}
                reason="Strong closing call-to-action"
              />

              <AssetClipCard
                type="video"
                sourceFile="brand_logo_animation.mp4"
                startTime="0:00"
                endTime="0:09"
                duration="0:09"
                transcript="[Logo animation with tagline: 'Innovate. Transform. Succeed.']"
                clipNumber={4}
              />
            </div>
          </div>
        </ScrollArea>
      </div>
    </div>
  );
}