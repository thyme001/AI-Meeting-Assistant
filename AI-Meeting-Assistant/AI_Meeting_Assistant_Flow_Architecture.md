# AI Meeting Assistant

## 1. Overview
AI Meeting Assistant is a web application designed to help users convert meeting discussions into structured summaries automatically. The system supports transcript input, participant management, meeting history, and AI-based analysis to generate useful outputs such as:

- Meeting information
- Key topics and decisions
- Action items grouped by owner
- Open issues and missing information
- Summary by topic

The application is implemented as a Streamlit web app and focuses on a simple, same-page workflow so users can enter data and view results without navigating to a separate result page.

---

## 2. System Architecture

```mermaid
flowchart LR
    U["ผู้ใช้ / เจ้าของการประชุม"] --> UI["หน้าเว็บ Streamlit\nแสดงฟอร์มและผลลัพธ์"]
    UI --> M1["1. ฟอร์มข้อมูลการประชุม\nชื่อการประชุม / วันที่"]
    UI --> M2["2. จัดการผู้เข้าร่วม\nเพิ่มชื่อและบทบาท"]
    UI --> M3["3. บันทึกการประชุม\nพิมพ์เองหรือใช้ไมค์"]
    UI --> M4["4. เปลี่ยนภาษาและธีม"]
    UI --> M5["5. ประวัติการประชุมด้านข้าง"]

    M3 --> B["ไมค์ Chrome / Web Speech API\nแปลงเสียงเป็นข้อความ"]
    B --> T["ข้อความถูกพิมพ์ลง textarea\nอัตโนมัติ"]
    M3 --> T
    M1 --> S["Session State\nเก็บข้อมูลชั่วคราว"]
    M2 --> S
    T --> S

    S --> A["กด Analyze Meeting\nตรวจสอบข้อมูลก่อนวิเคราะห์"]
    A --> L["AI Service Layer\nแยก UI และ Logic AI"]
    L --> P1["Mock AI\nทดสอบโครงสร้างผลลัพธ์"]
    L --> P2["Cohere / AI ฟรี\nสรุป transcript"]
    L --> P3["Fallback Summary\nสำรองเมื่อ AI หลักไม่ทำงาน"]
    L --> P4["Structured JSON Output\nหัวข้อ / ข้อตกลง / Action Items"]

    P4 --> F["Meeting Formatter\nจัดรูปแบบข้อมูลให้อ่านง่าย"]
    F --> R1["ข้อมูลการประชุม"]
    F --> R2["หัวข้อและคำตัดสิน"]
    F --> R3["งานที่ต้องทำ\nแยกตามคนรับผิดชอบ"]
    F --> R4["ประเด็นที่เปิด\nและข้อมูลที่ขาด"]
    F --> R5["สรุปตามหัวข้อ"]

    R1 --> O["แสดงผลบนหน้าเดียว\nไม่เปลี่ยนหน้า"]
    R2 --> O
    R3 --> O
    R4 --> O
    R5 --> O

    O --> H["บันทึกประวัติการประชุม"]
    H --> DB["Session History\nเก็บไว้ในหน่วยความจำ"]
```

> การอ่าน flow นี้คือ: ผู้ใช้กรอกข้อมูลการประชุม → ข้อมูลถูกเก็บไว้ใน Session State → กดวิเคราะห์ → ระบบส่งข้อมูลเข้าสู่ AI Service → AI สร้างสรุปแบบโครงสร้าง → Formatter จัดข้อมูลให้อ่านง่าย → แสดงผลบนหน้าเดียว → บันทึกประวัติไว้เพื่อดูย้อนหลัง

---

## 3. User Flow

```mermaid
flowchart TD
    A[Start] --> B[Create new meeting]
    B --> C[Input meeting title and date]
    C --> D[Add participants]
    D --> E[Enter transcript or use microphone]
    E --> F{Use voice input or manual typing?}
    F -->|Voice| G[Chrome speech recognition converts audio to text]
    F -->|Manual| H[Type transcript manually]
    G --> I[Text is inserted into transcript box automatically]
    H --> I
    I --> J[Click Analyze Meeting]
    J --> K[System sends data to AI analysis layer]
    K --> L[AI generates structured summary]
    L --> M[Result displayed on same page]
    M --> N[Save to meeting history]
    N --> O[Finish]
```

---

## 4. Functional Workflow

### 4.1 Frontend Layer
The web interface is built with Streamlit and includes:

- Meeting name and date form
- Transcript input area
- Participant management
- Meeting analysis button
- Theme toggle for light/dark mode
- Language switch for Thai/English
- Sidebar with meeting history

### 4.2 Input Layer
Users can provide meeting data by:

1. Typing transcript text manually, or
2. Using the Chrome microphone feature to convert speech to text automatically

The microphone input is handled by the browser Web Speech API, and the recognized text is inserted directly into the transcript field without the need for a backend API connection.

### 4.3 Processing Layer
Once the transcript and participant list are ready, the system sends the data to an AI analysis service. The analysis layer can work with:

- Mock AI for testing and demonstration
- Free AI / external provider fallback
- Structured-output generation for JSON-based summary extraction

This keeps the UI independent from the provider logic and allows the application to switch AI backends easily.

### 4.4 Formatter Layer
The analysis result is converted into a consistent output structure. The formatter organizes the data into the following sections:

- Meeting Information
- Topics and Decisions
- Action Items grouped by owner
- Open Issues and Missing Information
- Summary by Topic

### 4.5 Output Layer
The final results are displayed in the same page without redirecting to another page. This is designed for quick review and easier user interaction.

### 4.6 Persistence Layer
The system stores meeting summaries in session-based history for quick retrieval and review. This allows users to reload previous meeting reports without creating a separate database system in the MVP stage.

---

## 5. Business Logic Flow

```mermaid
flowchart LR
    A[Input transcript + participants] --> B[Validate required fields]
    B --> C{Valid data?}
    C -->|No| D[Show warning messages]
    C -->|Yes| E[Analyze meeting]
    E --> F[Generate structured summary]
    F --> G[Group action items by owner]
    G --> H[Render meeting summary UI]
    H --> I[Save to meeting history]
```

---

## 6. Major Components

### Streamlit UI
Handles the main interface and workflow:

- meeting creation
- transcript entry
- analysis trigger
- layout and theme control
- result display

### Session State
Stores the current values in memory, including:

- meeting name
- date
- transcript
- participants
- analysis output
- theme settings
- language settings
- history list

### AI Analysis Service
Responsible for converting raw transcript into structured meeting results. It acts as a boundary between the UI and the AI logic.

### Formatter Service
Responsible for shaping analysis results into a readable format and grouping items logically for output display.

---

## 7. Example of Result Output
The system produces output such as:

- Meeting Information
  - Meeting title
  - Date
  - Participants

- Topics & Decisions
  - Key topics discussed
  - Decisions made

- Action Items
  - Task name
  - Owner name
  - Follow-up responsibility

- Open Issues & Missing Information
  - Risks or unresolved items
  - Missing details or missing information needed

- Summary by Topic
  - A condensed overview of main discussion themes

---

## 8. Summary
The AI Meeting Assistant is a lightweight meeting summarization system built for fast use in a local MVP environment. It allows users to create meetings, input transcripts, use browser-based speech recognition, analyze discussions with AI or mock logic, and view structured summary results directly on the same page. The design keeps the system simple, user-friendly, and suitable for further extension with real AI APIs, database storage, and more advanced collaboration features in the future.

---

## 9. Project Status
Current implementation includes:

- same-page meeting analysis flow
- structured result display
- AI / mock analysis boundary
- owner-based action grouping
- language and theme switching
- meeting history sidebar
- Chrome microphone transcription support

This version is suitable for demonstration and functional prototype presentation.
