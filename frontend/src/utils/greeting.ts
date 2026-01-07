interface SpecialOccasion {
  month: number; // 0-11
  day: number;
  greeting: string;
}

const SPECIAL_OCCASIONS: SpecialOccasion[] = [
  { month: 0, day: 1, greeting: "Happy New Year" },
  { month: 1, day: 14, greeting: "Happy Valentine's Day" },
  { month: 2, day: 17, greeting: "Happy St. Patrick's Day" },
  { month: 3, day: 1, greeting: "Happy April Fools' Day" },
  { month: 3, day: 22, greeting: "Happy Earth Day" },
  { month: 4, day: 5, greeting: "Happy Cinco de Mayo" },
  { month: 4, day: 11, greeting: "Happy Mother's Day" }, // Second Sunday of May (approximate)
  { month: 5, day: 19, greeting: "Happy Juneteenth" },
  { month: 5, day: 20, greeting: "Happy Father's Day" }, // Third Sunday of June (approximate)
  { month: 6, day: 4, greeting: "Happy Independence Day" },
  { month: 9, day: 31, greeting: "Happy Halloween" },
  { month: 10, day: 11, greeting: "Happy Veterans Day" },
  { month: 10, day: 25, greeting: "Happy Thanksgiving" }, // Fourth Thursday of November (approximate)
  { month: 11, day: 24, greeting: "Merry Christmas Eve" },
  { month: 11, day: 25, greeting: "Merry Christmas" },
  { month: 11, day: 31, greeting: "Happy New Year's Eve" },
];

/**
 * Generates a personalized greeting based on time of day, special occasions, and user's name
 * @param userName - The user's first name
 * @param timezone - The user's timezone (e.g., "America/New_York")
 * @returns A personalized greeting string
 */
export function getGreeting(userName: string, timezone: string = "America/New_York"): string {
  try {
    // Get current date/time in user's timezone
    const now = new Date();
    const userTime = new Date(now.toLocaleString("en-US", { timeZone: timezone }));
    
    const hours = userTime.getHours();
    const month = userTime.getMonth();
    const day = userTime.getDate();

    // Check for special occasions first (within 2 days for multi-day celebrations)
    for (const occasion of SPECIAL_OCCASIONS) {
      if (occasion.month === month && Math.abs(occasion.day - day) <= 1) {
        return `${occasion.greeting}, ${userName}`;
      }
    }

    // Check if it's the user's birthday week (you'd get this from user profile)
    // This is a placeholder - in real app, check against user.birthMonth and user.birthDay
    // if (isBirthdayWeek(month, day, userBirthMonth, userBirthDay)) {
    //   return `Happy Birthday, ${userName}`;
    // }

    // Time-based greetings
    if (hours < 12) {
      return `Good morning, ${userName}`;
    } else if (hours < 17) {
      return `Good afternoon, ${userName}`;
    } else {
      return `Good evening, ${userName}`;
    }
  } catch (error) {
    // Fallback if timezone is invalid
    console.error("Invalid timezone:", timezone, error);
    return `Hello, ${userName}`;
  }
}

/**
 * Gets a contextual time-based greeting without the user's name
 */
export function getTimeGreeting(timezone: string = "America/New_York"): string {
  try {
    const now = new Date();
    const userTime = new Date(now.toLocaleString("en-US", { timeZone: timezone }));
    const hours = userTime.getHours();

    if (hours < 12) {
      return "Good morning";
    } else if (hours < 17) {
      return "Good afternoon";
    } else {
      return "Good evening";
    }
  } catch (error) {
    return "Hello";
  }
}
