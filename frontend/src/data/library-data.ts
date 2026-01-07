// Central source of truth for all library data and counts

export interface LibraryItem {
  id: string;
  fileName: string;
  description: string;
  keyPeople: string[];
  length: string;
  date: string;
}

// VIDEOS
export const MOCK_VIDEOS: LibraryItem[] = [
  {
    id: "1",
    fileName: "Q4_Product_Demo.mp4",
    description: "Product demo for Q4 launch presentation",
    keyPeople: ["Sarah Johnson", "Mike Chen"],
    length: "12:34",
    date: "Jan 3, 2026",
  },
  {
    id: "2",
    fileName: "Customer_Interview_Acme.mp4",
    description: "Customer feedback session with Acme Corp",
    keyPeople: ["David Lee", "Emma Watson"],
    length: "45:12",
    date: "Jan 2, 2026",
  },
  {
    id: "3",
    fileName: "Team_Standup_Dec_2025.mp4",
    description: "Weekly team standup meeting recording",
    keyPeople: ["Alex Chen", "Rachel Kim", "Tom Brown"],
    length: "18:45",
    date: "Dec 30, 2025",
  },
  {
    id: "4",
    fileName: "Marketing_Campaign_Review.mp4",
    description: "Review of Q4 marketing campaign performance",
    keyPeople: ["Lisa Park", "James Wilson"],
    length: "28:20",
    date: "Dec 28, 2025",
  },
];

// AUDIO
export const MOCK_AUDIO: LibraryItem[] = [
  {
    id: "1",
    fileName: "Podcast_Episode_12.mp3",
    description: "Interview with industry expert on AI trends",
    keyPeople: ["Alex Chen", "Dr. Sarah Martinez"],
    length: "52:18",
    date: "Jan 4, 2026",
  },
  {
    id: "2",
    fileName: "Voice_Note_Ideas.mp3",
    description: "Brainstorming session for new feature ideas",
    keyPeople: ["Mike Chen"],
    length: "8:45",
    date: "Jan 3, 2026",
  },
  {
    id: "3",
    fileName: "Client_Call_TechCorp.mp3",
    description: "Sales call with TechCorp discussing partnership",
    keyPeople: ["David Lee", "Emma Watson", "John Smith"],
    length: "34:12",
    date: "Dec 29, 2025",
  },
];

// TRANSCRIPTS
export const MOCK_TRANSCRIPTS: LibraryItem[] = [
  {
    id: "1",
    fileName: "Q4_Product_Demo_Transcript.txt",
    description: "Transcript of Q4 product demo presentation",
    keyPeople: ["Sarah Johnson", "Mike Chen"],
    length: "3,245 words",
    date: "Jan 3, 2026",
  },
  {
    id: "2",
    fileName: "Customer_Interview_Acme_Transcript.txt",
    description: "Transcript of Acme Corp customer feedback session",
    keyPeople: ["David Lee", "Emma Watson"],
    length: "8,912 words",
    date: "Jan 2, 2026",
  },
  {
    id: "3",
    fileName: "Podcast_Episode_12_Transcript.txt",
    description: "Transcript of AI trends podcast episode",
    keyPeople: ["Alex Chen", "Dr. Sarah Martinez"],
    length: "12,456 words",
    date: "Jan 4, 2026",
  },
  {
    id: "4",
    fileName: "Team_Meeting_Notes.txt",
    description: "Notes from weekly team standup meeting",
    keyPeople: ["Alex Chen", "Rachel Kim", "Tom Brown"],
    length: "1,823 words",
    date: "Dec 30, 2025",
  },
];

// PDFS
export const MOCK_PDFS: LibraryItem[] = [
  {
    id: "1",
    fileName: "Product_Roadmap_2026.pdf",
    description: "Comprehensive product roadmap for 2026",
    keyPeople: ["Sarah Johnson", "Product Team"],
    length: "24 pages",
    date: "Jan 5, 2026",
  },
  {
    id: "2",
    fileName: "Market_Research_Report.pdf",
    description: "Q4 2025 market research and competitive analysis",
    keyPeople: ["Lisa Park", "Research Team"],
    length: "45 pages",
    date: "Jan 2, 2026",
  },
  {
    id: "3",
    fileName: "Customer_Success_Metrics.pdf",
    description: "Customer success KPIs and performance metrics",
    keyPeople: ["Emma Watson", "CS Team"],
    length: "12 pages",
    date: "Dec 31, 2025",
  },
  {
    id: "4",
    fileName: "Engineering_Architecture_Doc.pdf",
    description: "Technical architecture documentation for new platform",
    keyPeople: ["Mike Chen", "Engineering Team"],
    length: "67 pages",
    date: "Dec 28, 2025",
  },
];

// HELPER FUNCTIONS TO GET COUNTS
export function getLibraryCount(type: "videos" | "audio" | "transcripts" | "pdfs"): number {
  switch (type) {
    case "videos":
      return MOCK_VIDEOS.length;
    case "audio":
      return MOCK_AUDIO.length;
    case "transcripts":
      return MOCK_TRANSCRIPTS.length;
    case "pdfs":
      return MOCK_PDFS.length;
  }
}

export function getLibraryItems(type: "videos" | "audio" | "transcripts" | "pdfs"): LibraryItem[] {
  switch (type) {
    case "videos":
      return MOCK_VIDEOS;
    case "audio":
      return MOCK_AUDIO;
    case "transcripts":
      return MOCK_TRANSCRIPTS;
    case "pdfs":
      return MOCK_PDFS;
  }
}

export function getTotalLibraryCount(): number {
  return MOCK_VIDEOS.length + MOCK_AUDIO.length + MOCK_TRANSCRIPTS.length + MOCK_PDFS.length;
}
