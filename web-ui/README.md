# TMF Product Catalog - Web UI

A modern, responsive, and "snappy" management portal and shopping interface for the TMF Product Catalog System. Built with the latest frontend technologies for a premium enterprise experience.

---

## 🛠 Technology Stack

- **Framework:** [Next.js 16.1.3](https://nextjs.org/) (App Router, React 19)
- **Styling:** [Tailwind CSS 4.1.18](https://tailwindcss.com/) (Modern CSS-first approach)
- **Animations:** [Framer Motion](https://www.framer.com/motion/) (For smooth, high-end transitions)
- **Icons:** [Lucide React](https://lucide.dev/)
- **Forms:** [React Hook Form](https://react-hook-form.com/) + [Zod](https://zod.dev/) (Type-safe validation)
- **Notifications:** [React Hot Toast](https://react-hot-toast.com/)
- **Testing:** [Vitest](https://vitest.dev/) + [React Testing Library](https://testing-library.com/docs/react-testing-library/intro/)

---

## ✨ Key Features

### 1. Secure Authentication
- JWT-based authentication flow.
- Token storage in `localStorage` with automatic attachment to API requests.
- Protected routes using a custom `ProtectedRoute` wrapper.
- Automatic 401 redirect to login.

### 2. The Builder (Admin Management)
- **Dynamic Forms:** Multi-step-like creation of Characteristics, Specifications, Pricing, and Offerings.
- **Dependency Management:** Real-time fetching of required entities (e.g., Specs need Characteristics).
- **Saga Integration:** One-click publishing that triggers and polls the backend distributed transaction.

### 3. The Viewer (Entity Explorer)
- **Generic DataTable:** Searchable, sortable, and paginated tables for all entities.
- **Deep Hierarchy:** Expandable views to see full Offering → Specification → Characteristic relationships.
- **Smart Actions:** 
  - Edit/Delete with pre-filled forms.
  - Lifecycle management (Publish/Retire offerings).
  - Direct "Publish Now" with real-time status polling.
  - Safety locks (Prices are read-only when used in published offerings).

### 4. The Store (Public Marketplace)
- **Public Catalog:** Browse published offerings without logging in.
- **Advanced Filtering:** Keyword search, price range, and sales channel filters.
- **URL Synchronization:** Filters and search queries are stored in the URL for easy sharing.
- **Offering Detail:** Immersive view of product details, specifications, and pricing.

### 5. Enterprise UI/UX
- **Orange Branding:** Custom accent colors inspired by the "Orange" telecom brand.
- **Micro-animations:** Subtle hover effects and layout transitions to enhance feel.
- **Responsive:** Desktop-first design that scales down gracefully.

---

## 📂 Project Structure

```text
web-ui/
├── src/
│   ├── app/              # Next.js App Router (Pages & Layouts)
│   ├── components/       # UI Components
│   │   ├── forms/        # Entity-specific forms (Reusable)
│   │   ├── ui/           # Generic base components (DataTable, Modal, etc.)
│   ├── contexts/         # React Contexts (AuthContext)
│   ├── lib/              # Utilities (API Client, helper functions)
│   └── test/             # Test setup and mocks
├── public/               # Static assets
└── tailwind.config.ts    # Custom branding & animations
```

---

## 🚀 Getting Started

### 1. Install Dependencies
```bash
npm install
```

### 2. Configure Environment
Create a `.env.local` file:
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 3. Run Development Server
```bash
npm run dev
```
*The app will be available at [http://localhost:3000](http://localhost:3000)*

### 4. Build for Production
```bash
npm run build
npm run start
```

---

## 🧪 Testing

We use Vitest for fast, reliable component testing.

```bash
# Run all tests
npm run test

# Run tests in UI mode
npx vitest --ui
```

---

## 🎨 Branding Note
This UI uses `#FF7900` (Orange Brand) as its primary accent color, providing a professional and energetic telecom-industry aesthetic.
