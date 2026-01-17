# PART II: FRONTEND REQUIREMENTS

## 1. INTRODUCTION

### 1.1 Purpose
The frontend is a modern single-page application (SPA) that provides user interface for managing product catalog entities and viewing published offerings in a customer-facing store.

### 1.2 Technology Stack
- **Framework:** Next.js 16+ (React 19+, App Router)
- **Styling:** Tailwind CSS 4+
- **HTTP Client:** Fetch API or Axios
- **State Management:** React Context API or Zustand (optional)
- **Form Handling:** React Hook Form (optional)
- **UI Components:** Headless UI or shadcn/ui (optional)

### 1.3 Architectural Pattern
- Single Page Application (SPA)
- Communicates exclusively with API Gateway (no direct service calls)
- Client-side routing via Next.js App Router
- JWT token stored in localStorage or httpOnly cookies
- Responsive design (desktop-first, mobile-friendly)

---

## 2. PAGE STRUCTURE

### 2.1 Application Layout

**Main Navigation:**
- Builder (create entities)
- Viewer (browse entities)
- Store (customer catalog)
- Login/Logout

**Header:**
- Application logo/title
- Navigation menu
- User indicator (username, role)
- Logout button

**Footer:** Simple copyright notice (optional)

---

## 3. USER FLOWS & STORIES

### 3.1 Authentication Flow

**Story:** User must login before accessing Builder/Viewer pages

**Steps:**
1. User visits application → Redirected to /login
2. User enters username and password
3. System validates credentials → Returns JWT token
4. Token stored in browser (localStorage)
5. User redirected to Builder page
6. All API requests include Authorization header with token
7. On token expiration, redirect to login

**UI Requirements:**
- Login page: Username field, password field, login button
- Error message display for invalid credentials
- Loading indicator during authentication

---

### 3.2 Builder Page

**Story:** Admin creates characteristics, specifications, prices, and offerings

**Layout:** Tab-based interface with 4 tabs

#### Tab 1: Create Characteristic
**Form Fields:**
- Name (text input, required)
- Value (text input, required)
- Unit of Measure (dropdown: Mbps, GB, GHz, Volt, Watt, Meter, None)
- Create button

**Behavior:**
- On submit → POST /api/v1/characteristics
- On success → Show success toast, clear form
- On error → Display error message below form
- Validation: Client-side (required fields) + server-side errors

#### Tab 2: Create Specification
**Form Fields:**
- Name (text input, required)
- Characteristics (multi-select dropdown with search)
  - Fetch existing characteristics: GET /api/v1/characteristics
  - Display: "Speed (100 Mbps)", "Storage (256 GB)"
  - Minimum 1 selection required
- Create button

**Behavior:**
- On mount → Fetch characteristics for dropdown
- On submit → POST /api/v1/specifications with characteristic IDs
- Handle loading state for async operations
- Display selected characteristics as chips/tags

#### Tab 3: Create Pricing
**Form Fields:**
- Name (text input, required)
- Value (number input, 2 decimals, required)
- Unit (text input, e.g., "per month", required)
- Currency (dropdown: USD, EUR, TRY)
- Create button

**Behavior:**
- Standard form submission to POST /api/v1/prices
- Validate positive decimal value client-side

#### Tab 4: Create Product Offering
**Form Fields:**
- Name (text input, required)
- Description (textarea, optional)
- Specifications (multi-select dropdown)
  - Fetch: GET /api/v1/specifications
  - Display: Spec name
- Pricing (multi-select dropdown)
  - Fetch: GET /api/v1/prices
  - Field name: `pricing_ids` (matches backend API)
  - Display: Price name and value
- Sales Channels (multi-select or checkboxes: Online, Retail, Partner)
- Lifecycle Status (display only, starts as DRAFT)
- Save Draft button (creates offering in DRAFT state)
- Publish button (enabled only if all fields valid)

**Behavior:**
- Save Draft → POST /api/v1/offerings (partial data allowed)
- Publish → POST /api/v1/offerings/{id}/publish
  - Show loading spinner during saga execution
  - Poll offering status every 2 seconds until PUBLISHED or FAILED
  - Display success/failure message
  - If failed, show error details from saga

**Validation:**
- Draft: Only name required
- Publish: Name, at least 1 spec, 1 price (pricing_ids), 1 sales channel required

---

### 3.3 Viewer Page

**Story:** User browses existing entities to see what's been created

**Layout:** Tab-based interface with 4 tabs (read-only views)

#### Tab 1: View Characteristics
**Display:**
- Table or card grid showing all characteristics
- Columns: Name, Value, Unit, Created Date
- Pagination (20 per page)
- Search/filter by name (client-side or server-side)
- Edit button (opens modal with form)
- Delete button (with confirmation dialog)

**API Calls:**
- GET /api/v1/characteristics (on mount)
- PUT /api/v1/characteristics/{id} (edit)
- DELETE /api/v1/characteristics/{id} (delete)

**Delete Behavior:**
- If referenced by specs → Show error "Cannot delete, used by specifications"

#### Tab 2: View Specifications
**Display:**
- Table/grid with: Name, Characteristics (comma-separated), Created Date
- Click to expand and show full characteristic details
- Edit and delete buttons
- Pagination

**Characteristic Display:**
- "Speed: 100 Mbps, Storage: 256 GB"
- Expandable to show all characteristics in list format

#### Tab 3: View Prices
**Display:**
- Table: Name, Value, Unit, Currency, Status (Locked/Unlocked)
- Edit and delete buttons
- If locked, show lock icon and tooltip "Locked by offering publication"
- Pagination

#### Tab 4: View Offerings
**Display:**
- Table/cards with: Name, Lifecycle Status (badge), Published Date
- Filter by lifecycle status (All, Draft, Published, Retired)
- Click to view full details (modal or detail page)
- Actions based on status:
  - DRAFT: Edit button, Publish button, Delete button
  - PUBLISHED: Retire button, View Details button
  - RETIRED: View Details button only

**Detail View:**
- Show all offering information
- Expand specs and prices with full details
- Show publication/retirement dates

---

### 3.4 Store Page

**Story:** Customers browse published product offerings with search and filters

**Layout:** Single-page catalog view

**Components:**

#### Search Bar
- Text input for full-text search
- Search button or auto-search on typing

#### Filters Panel (Sidebar or Collapsible)
- Price range slider (min/max)
- Characteristic filters (dynamic based on available characteristics)
  - Example: Speed dropdown (< 50 Mbps, 50-100, > 100)
- Sales channel checkboxes
- Clear filters button

#### Results Grid
- Card layout (3-4 columns on desktop, 1-2 on mobile)
- Each card shows:
  - Offering name
  - Price (highlight lowest if multiple)
  - Key characteristics (top 3)
  - "View Details" button

**Card Click Behavior:**
- Expand card in place OR navigate to detail page
- Show full specifications with all characteristics
- Show all pricing options
- Show sales channels

#### Detail View
- Large modal or dedicated page
- Full offering information in organized layout
- Specifications section with expandable characteristics
- Pricing section showing all price tiers
- Sales channels indicators

#### Pagination/Infinite Scroll
- Load more button or infinite scroll
- Show "Showing X of Y results"

**API Calls:**
- GET /api/v1/store/offerings?query=...&min_price=...&characteristic=...
- Debounce search queries (300ms delay)

**No Authentication Required:** Store page is public-facing

---

## 4. UI/UX REQUIREMENTS

### 4.1 Visual Design
- **Color Scheme:** Professional (blue/gray tones for business app)
- **Typography:** Clear, readable fonts (Inter, Roboto, or system fonts)
- **Spacing:** Consistent padding/margins (Tailwind spacing scale)
- **Buttons:** Primary (blue), secondary (gray), danger (red)
- **Forms:** Clear labels, inline validation, error states

### 4.2 Responsive Design
- Desktop: Full layout with sidebars, wide tables
- Tablet: Adjusted layouts, collapsible sidebars
- Mobile: Stacked layout, hamburger menu, touch-friendly buttons
- Breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)

### 4.3 Loading States
- Skeleton screens for initial page load
- Spinners for button actions (submit, delete)
- Loading indicators for dropdowns fetching data
- Disable buttons during async operations

### 4.4 Error Handling
- Toast notifications for success/error messages (top-right corner)
- Inline form errors (red text below field)
- Network error fallback (retry button)
- 404 page for invalid routes
- Unauthorized redirect to login

### 4.5 Accessibility
- Semantic HTML (form labels, headings hierarchy)
- Keyboard navigation support (tab through forms)
- ARIA labels for icons/buttons
- Color contrast compliance (WCAG AA)
- Focus indicators visible

---

## 5. STATE MANAGEMENT

### 5.1 Authentication State
- Store JWT token and user info (username, role)
- Provide via React Context to all components
- Logout clears token and redirects

### 5.2 Form State
- Use controlled components (React state)
- Validation state (errors, touched fields)
- Submission state (loading, success, error)

### 5.3 Data Fetching
- Fetch on component mount (useEffect)
- Cache responses (optional: React Query or SWR)
- Refetch after mutations (create, update, delete)

### 5.4 Filter State (Store Page)
- URL query parameters for filters (enables bookmarking)
- Example: `/store?query=internet&min_price=10&max_price=100`
- Update URL on filter change (Next.js router)

---

## 6. API INTEGRATION

### 6.1 HTTP Client Configuration
- Base URL: API Gateway (http://localhost:8000)
- Default headers: Content-Type: application/json
- Authorization header: Bearer {token} (from auth state)
- Timeout: 30 seconds

### 6.2 Error Response Handling
- Parse error JSON: `{ error: { code, message, details } }`
- Display user-friendly messages
- Log errors to console (development)
- Retry on network errors (optional)

### 6.3 Request/Response Flow
```
User Action → Form Submit
  → Validate Client-Side
  → Send HTTP Request (with JWT)
  → Show Loading State
  → Receive Response
    → Success: Show toast, update UI, clear form
    → Error: Display error message, keep form data
```

---

## 7. ROUTING STRUCTURE

```
/                       → Redirect to /login or /builder (if authenticated)
/login                  → Login page (public)
/builder                → Builder page with 4 tabs (protected)
  /builder?tab=characteristic
  /builder?tab=specification
  /builder?tab=pricing
  /builder?tab=offering
/viewer                 → Viewer page with 4 tabs (protected)
  /viewer?tab=characteristic
  /viewer?tab=specification
  /viewer?tab=pricing
  /viewer?tab=offering
/store                  → Store catalog page (public)
/store/offerings/{id}   → Offering detail page (optional, public)
```

**Protected Routes:** Redirect to /login if no JWT token

---

## 8. COMPONENT STRUCTURE (High-Level)

```
/web-ui
├── src/
│   ├── app/                      # Next.js App Router (v16)
│   │   ├── layout.tsx            # Root layout with nav/header
│   │   ├── page.tsx              # Home redirect (authenticated → /builder, unauthenticated → /login)
│   │   ├── login/
│   │   │   └── page.tsx          # Login form
│   │   ├── builder/
│   │   │   └── page.tsx          # Builder with tabs
│   │   ├── viewer/
│   │   │   └── page.tsx          # Viewer with tabs
│   │   └── store/
│   │       └── page.tsx          # Store catalog (public)
│   │
│   ├── components/               # Reusable UI components
│   │   ├── Header.tsx            # Navigation header with mounted state for hydration safety
│   │   ├── ui/
│   │   │   ├── Tabs.tsx
│   │   │   ├── FilterPanel.tsx
│   │   │   ├── OfferingCard.tsx
│   │   │   ├── OfferingDetail.tsx
│   │   │   ├── Modal.tsx
│   │   │   ├── MultiSelect.tsx
│   │   │   └── ...
│   │   └── forms/
│   │       ├── CharacteristicForm.tsx
│   │       ├── SpecificationForm.tsx
│   │       ├── PricingForm.tsx
│   │       └── OfferingForm.tsx     # Uses pricing_ids field
│   │
│   ├── lib/                      # Utilities
│   │   ├── api-client.ts         # HTTP client wrapper
│   │   ├── hooks.ts              # Custom React hooks (useSagaPolling)
│   │   └── utils.ts              # Helper functions (cn for classnames)
│   │
│   └── contexts/
│       └── AuthContext.tsx       # Auth state provider with JWT handling
│
├── public/                       # Static assets
├── tailwind.config.ts
└── package.json
```

---

## 9. KEY IMPLEMENTATION NOTES

### 9.1 Multi-Select Dropdowns
- Library recommendation: react-select or Headless UI Combobox
- Features: Search/filter, multi-select, display selected as chips
- Fetch options on mount, cache in component state

### 9.2 Saga Status Polling
```typescript
// Pseudo-code for offering publication
async function publishOffering(id: string) {
  await api.post(`/offerings/${id}/publish`);
  
  // Poll for status
  const maxAttempts = 30; // 1 minute max
  for (let i = 0; i < maxAttempts; i++) {
    await sleep(2000);
    const offering = await api.get(`/offerings/${id}`);
    
    if (offering.lifecycle_status === 'PUBLISHED') {
      showSuccess('Offering published successfully!');
      return;
    }
    if (offering.lifecycle_status === 'DRAFT') {
      showError('Publication failed, offering reverted to draft');
      return;
    }
  }
  showWarning('Publication taking longer than expected');
}
```

### 9.3 Filter Building (Store Page)
```typescript
// Build query string from filter state
const filters = {
  query: 'internet',
  min_price: 10,
  max_price: 100,
  characteristic: 'Speed:>50Mbps'
};

const queryString = new URLSearchParams(filters).toString();
const url = `/api/v1/store/offerings?${queryString}`;
```

### 9.4 Token Expiration Handling
- Intercept 401 responses globally
- Clear token and redirect to login
- Optional: Implement token refresh before expiration

---

## 10. TESTING STRATEGY (Frontend)

### 10.1 Component Testing (Optional)
- Tool: Vitest + React Testing Library
- Test: Form validation, button states, conditional rendering
- Focus on critical user interactions

### 10.2 E2E Testing (Optional)
- Tool: Playwright or Cypress
- Test: Login flow, create characteristic, publish offering
- Run against live backend (Docker Compose)

### 10.3 Manual Testing Checklist
- [ ] Login with valid/invalid credentials
- [ ] Create characteristic and see in viewer
- [ ] Create specification with characteristic dependency
- [ ] Create pricing
- [ ] Create draft offering (partial data)
- [ ] Edit draft offering
- [ ] Publish offering (wait for saga completion)
- [ ] See published offering in Store
- [ ] Search and filter in Store
- [ ] Retire offering and verify removal from Store
- [ ] Test on different screen sizes (responsive)
- [ ] Test error scenarios (network failure, validation errors)

---

## 11. DEVELOPMENT WORKFLOW

### 11.1 Setup

**Recommended Method (Makefile):**
```bash
# Start backend and frontend together
make dev

# Start frontend only
make frontend
```

**Manual Setup:**
```bash
cd web-ui
npm install
npm run dev  # Starts on localhost:3000
```

### 11.2 Environment Variables
```bash
# .env.local
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

### 11.3 Build & Deploy
```bash
npm run build      # Production build
npm run start      # Serve production build
docker build -t product-catalog-ui .
```

---

## 12. SUCCESS CRITERIA (Frontend)

The frontend is complete when:

1. ✅ All 4 pages implemented (Login, Builder, Viewer, Store)
2. ✅ Authentication flow works (login, token storage, logout)
3. ✅ Builder page creates all 4 entity types
4. ✅ Viewer page displays all entities with edit/delete
5. ✅ Store page shows published offerings with search/filter
6. ✅ Cross-service validation works (spec requires existing chars)
7. ✅ Saga status polling implemented (publish offering)
8. ✅ Loading and error states handled gracefully
9. ✅ Responsive design works on mobile and desktop
10. ✅ UI is visually polished and professional
11. ✅ No console errors during normal operation
12. ✅ Complete user journey executable in demo video

---

## 13. IMPLEMENTATION DETAILS (Phase 17 Updates)

### 13.1 Store Page (Public Catalog)
- **Public Access:** No authentication required to browse the marketplace.
- **Advanced Search:** Real-time keyword search across names, descriptions, and specifications.
- **Nested Filtering:** 
    - Price range filtering using nested Elasticsearch queries.
    - Dynamic sales channel filtering.
- **State Persistence:** All filters are synchronized with URL query parameters for bookmarkable search results.
- **Infinite Browsing:** "Load More" pagination for seamless discovery.

### 13.2 Saga UX Enhancements
- **Real-time Feedback:** Automatic status polling when initiating publication from Builder or Viewer.
- **Visual Indicators:** Loading spinners and status-aware buttons during the distributed transaction.
- **Toast Notifications:** Success/Error toasts with specific feedback from the saga completion.

---

## 14. OPTIONAL ENHANCEMENTS (If Time Permits)

- Real-time updates via WebSockets (when offerings published by others)
- Advanced search with autocomplete suggestions
- Export offerings as JSON/CSV
- Bulk operations (delete multiple characteristics)
- Dark mode toggle
- Internationalization (multi-language support)
- Offering comparison feature (side-by-side view)
- Admin dashboard with statistics (total offerings, published count)

---

# FINAL NOTES

## Project Submission Checklist

### Code Deliverables
- [ ] Monorepo with all services
- [ ] Docker Compose file (working, documented)
- [ ] Database migrations (Alembic scripts)
- [ ] Shared chassis library
- [ ] Camunda BPMN files
- [ ] Frontend application
- [ ] README with setup instructions
- [ ] .env.example file

### Documentation (Report)
- [ ] Problem definition (TMF catalog requirements)
- [ ] User stories and scenarios
- [ ] Non-functional requirements
- [ ] Architecture diagrams (context, container, component)
- [ ] Service decomposition rationale (bounded contexts)
- [ ] Design patterns applied (CQRS, Saga, Outbox, etc.)
- [ ] Technology stack justification
- [ ] Database schemas
- [ ] API endpoints documentation
- [ ] Testing strategy and results
- [ ] Deployment instructions
- [ ] Evaluation and future improvements

### Demo Video (Max 5 Minutes)
1. Architecture overview (diagram) - 30s
2. Live demo walkthrough:
   - Login - 10s
   - Create characteristic - 20s
   - Create specification (show dependency) - 20s
   - Create pricing - 20s
   - Create and publish offering (show saga) - 60s
   - View in Store page - 30s
   - Show search/filter - 20s
3. Technical highlights:
   - Open Camunda Cockpit (show process) - 30s
   - Open Zipkin (show trace) - 30s
   - Open Kibana (show logs with correlation ID) - 20s
4. Conclusion - 20s

**Total: ~5 minutes**

---

## Grading Criteria Alignment

Based on typical microservices course grading:

**Architecture Design (30%):**
- Clear bounded contexts ✅
- Proper service decomposition ✅
- Pattern application (CQRS, Saga, Outbox, API Gateway, Circuit Breaker) ✅

**Implementation Quality (40%):**
- Clean Architecture adherence ✅
- DDD with rich domain models ✅
- Database-per-service ✅
- Event-driven communication ✅
- Transactional consistency ✅

**Testing (15%):**
- Unit, integration, component, E2E tests ✅
- Coverage reporting ✅

**Observability (10%):**
- Distributed tracing ✅
- Log aggregation ✅
- Health checks ✅

**Documentation & Presentation (5%):**
- Comprehensive report ✅
- Clear demo video ✅

---

**END OF REQUIREMENTS SPECIFICATION**

This document serves as the complete blueprint for implementing the TMF Product Catalog Microservices System. All architectural decisions, business rules, technical requirements, and implementation guidelines are specified to enable autonomous development by AI agents or human developers.