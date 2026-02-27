<template>
  <div class="dashboard">
    <!-- Top Tab Bar -->
    <div class="tab-bar-container" v-if="tabsLoaded">
      <div class="tab-bar">
        <div class="tabs-section">
        <div
          v-for="(tab, index) in tabs"
          :key="tab.id"
          :class="['tab-wrapper', { active: activeTab === tab.id, dragging: draggedTabId === tab.id, 'drag-over': dragOverIndex === index }]"
          @dragover.prevent="handleDragOver($event, index)"
          @dragenter.prevent="dragOverIndex = index"
          @dragleave="handleDragLeave($event, index)"
          @drop="handleDrop($event, index)"
          @contextmenu.prevent="showTabContextMenu($event, tab)"
        >
          <span
            v-if="!editingTab || editingTab.id !== tab.id"
            class="tab-drag-handle"
            draggable="true"
            @dragstart="handleDragStart($event, tab, index)"
            @dragend="handleDragEnd"
            title="Trascina per riordinare"
          >
            <span class="divider-line"></span>
          </span>
          <button
            :class="['tab-btn', { active: activeTab === tab.id }]"
            @click="setActiveTab(tab.id)"
            @dblclick="startRenameTab(tab)"
          >
            <template v-if="!editingTab || editingTab.id !== tab.id">
              <span>{{ tab.name }}</span>
              <span v-if="tab.sharedSession?.active" class="tab-live-pill">LIVE</span>
            </template>
            <input
              v-else
              v-model="editingTabName"
              @blur="finishRenameTab"
              @keyup.enter="finishRenameTab"
              @keyup.esc="cancelRenameTab"
              class="tab-rename-input"
              @click.stop
            />
          </button>

        </div>
        <button class="add-tab-btn" @click="showTabWizard = true">+</button>
      </div>
        <UserProfile
          :username="currentUser?.username"
          :email="currentUser?.email"
          :is-logged-in="isLoggedIn"
          :profile-picture-url="currentUser?.profile_picture_url"
          @login="showLoginModal = true"
          @register="showRegisterModal = true"
          @logout="handleLogout"
          @profile="handleViewProfile"
        />
      </div>
    </div>
    
    <!-- Loading bar durante il caricamento iniziale -->
    <div v-else class="tab-bar-container loading-bar">
      <div class="tab-bar">
        <div class="tabs-section">
          <div class="loading-tabs-placeholder"></div>
        </div>
        <UserProfile
          :username="currentUser?.username"
          :email="currentUser?.email"
          :is-logged-in="isLoggedIn"
          :profile-picture-url="currentUser?.profile_picture_url"
          @login="showLoginModal = true"
          @register="showRegisterModal = true"
          @logout="handleLogout"
          @profile="handleViewProfile"
        />
      </div>
    </div>

    <!-- Tab Content -->
    <div class="tab-content">
      <!-- Loading state durante il caricamento iniziale -->
      <div v-if="!tabsLoaded || activeTab === null" class="tabs-loading">
        <div class="loading-spinner"></div>
      </div>
      
      <template v-else>

      <!-- News Tab -->
      <div
        v-for="tab in tabs"
        :key="'news-' + tab.id"
        v-show="activeTab === tab.id && tab.type === 'news'"
        class="tab-panel news-panel"
      >
        <NewsFeed />
      </div>

      <!-- Bot Tab -->
      <div
        v-for="tab in tabs"
        :key="'bot-' + tab.id"
        v-show="activeTab === tab.id && tab.type === 'bot'"
        class="tab-panel bot-panel"
      >
        <BotList 
          @view-bot="handleViewBot"
          @compete="handleCompete"
          @create-bot="handleCreateBot"
        />
      </div>

      <!-- Chat Tab -->
      <div
        v-for="tab in tabs"
        :key="'chat-' + tab.id"
        v-show="activeTab === tab.id && (tab.type === 'chat' || tab.type === 'flex')"
        class="tab-panel flex-panel"
      >
        <FlexChat 
          :tab-id="tab.id" 
          :initial-config="tab.chatConfig"
          :shareable-tabs="shareableTabs"
          :get-tab-snapshot="getTabSnapshot"
          :active-tab-id="activeTab"
          @open-shared-tab="handleOpenSharedTab"
          @share-started="handleShareStarted"
          @update-config="(config) => updateTabConfig(tab.id, config)" 
        />
      </div>

      <!-- Strategy Tab -->
      <div
        v-for="tab in tabs"
        :key="'strategy-' + tab.id"
        v-show="activeTab === tab.id && tab.type === 'strategy'"
        class="tab-panel strategy-panel"
      >
        <div v-if="tab.sharedSession" class="shared-tab-banner">
          <div class="shared-tab-info">
            <span class="shared-tab-dot"></span>
            <span class="shared-tab-title">Live: {{ tab.sharedSession.tab_name || tab.name }}</span>
            <span class="shared-tab-count">{{ getSharedParticipantsCount(tab.sharedSession.share_id) }} online</span>
          </div>
          <div class="shared-tab-actions">
            <button v-if="tab.sharedSession.isOwner" class="shared-tab-stop" @click="stopSharingTab(tab.id)">Ferma</button>
            <span v-else class="shared-tab-guest">Collaborazione live</span>
          </div>
        </div>
        <StrategyBuilder 
          :shared-state="tab.strategyState"
          :read-only="false"
          @state-change="(state) => handleStrategyStateChange(tab.id, state)"
          @save="saveUserTabs"
        />
      </div>

      <!-- Earnings Tab -->
      <div
        v-for="tab in tabs"
        :key="'earnings-' + tab.id"
        v-show="activeTab === tab.id && tab.type === 'earnings'"
        class="tab-panel earnings-panel"
      >
        <EarningsList />
      </div>

      <!-- Backtesting Tab -->
      <div
        v-for="tab in tabs"
        :key="'backtesting-' + tab.id"
        v-show="activeTab === tab.id && tab.type === 'backtesting'"
        class="tab-panel backtesting-panel"
      >
        <div v-if="tab.sharedSession" class="shared-tab-banner">
          <div class="shared-tab-info">
            <span class="shared-tab-dot"></span>
            <span class="shared-tab-title">Live: {{ tab.sharedSession.tab_name || tab.name }}</span>
            <span class="shared-tab-count">{{ getSharedParticipantsCount(tab.sharedSession.share_id) }} online</span>
          </div>
          <div class="shared-tab-actions">
            <button v-if="tab.sharedSession.isOwner" class="shared-tab-stop" @click="stopSharingTab(tab.id)">Ferma</button>
            <span v-else class="shared-tab-guest">Collaborazione live</span>
          </div>
        </div>
        <BacktestingPanel
          :shared-state="tab.backtestingState"
          :read-only="false"
          @state-change="(state) => handleBacktestingStateChange(tab.id, state)"
        />
      </div>

      <!-- Stocks Tab -->
      <div
        v-for="tab in tabs"
        :key="tab.id"
        v-show="activeTab === tab.id && tab && tab.type === 'stocks'"
        class="tab-panel"
      >
        <div v-if="tab.sharedSession" class="shared-tab-banner">
          <div class="shared-tab-info">
            <span class="shared-tab-dot"></span>
            <span class="shared-tab-title">Live: {{ tab.sharedSession.tab_name || tab.name }}</span>
            <span class="shared-tab-count">{{ getSharedParticipantsCount(tab.sharedSession.share_id) }} online</span>
          </div>
          <div class="shared-tab-actions">
            <button v-if="tab.sharedSession.isOwner" class="shared-tab-stop" @click="stopSharingTab(tab.id)">Ferma</button>
            <span v-else class="shared-tab-guest">Collaborazione live</span>
          </div>
        </div>
        <!-- Chart Info Bar -->
        <div v-if="tab && tab.chartInfo" class="chart-info-bar">
          <!-- Ticker Identity -->
          <div class="info-ticker">
            <span class="ticker-symbol">{{ tab.chartInfo.symbol || '--' }}</span>
            <span class="ticker-name">{{ tab.chartInfo.name || '--' }}</span>
          </div>

          <!-- Main Price Display -->
          <div class="info-price-main">
            <span :class="['main-price', { positive: tab.chartInfo.changePercent > 0, negative: tab.chartInfo.changePercent < 0 }]">
              {{ tab.chartInfo.price ? tab.chartInfo.price.toFixed(2) : '--' }}
            </span>
            <div class="price-change">
              <span :class="['change-value', { positive: tab.chartInfo.change > 0, negative: tab.chartInfo.change < 0 }]">
                {{ tab.chartInfo.change ? (tab.chartInfo.change > 0 ? '+' : '') + tab.chartInfo.change.toFixed(2) : '--' }}
              </span>
              <span :class="['change-percent', { positive: tab.chartInfo.changePercent > 0, negative: tab.chartInfo.changePercent < 0 }]">
                ({{ tab.chartInfo.changePercent ? (tab.chartInfo.changePercent > 0 ? '+' : '') + tab.chartInfo.changePercent.toFixed(2) + '%' : '--' }})
              </span>
            </div>
            <span :class="['market-badge', tab.chartInfo.marketState?.toLowerCase() || 'closed']">
              {{ tab.chartInfo.marketState === 'REGULAR' ? 'LIVE' : tab.chartInfo.marketState === 'POST' ? 'AFTER HRS' : tab.chartInfo.marketState === 'PRE' ? 'PRE-MKT' : 'CLOSED' }}
            </span>
          </div>

          <!-- Extended Hours Price (After Hours / Pre-Market) -->
          <div v-if="tab.chartInfo.postMarketPrice || tab.chartInfo.preMarketPrice" class="info-extended-hours">
            <template v-if="tab.chartInfo.postMarketPrice">
              <span class="extended-label">AH</span>
              <span :class="['extended-price', { positive: tab.chartInfo.postMarketChange > 0, negative: tab.chartInfo.postMarketChange < 0 }]">
                {{ tab.chartInfo.postMarketPrice?.toFixed(2) }}
              </span>
              <span :class="['extended-change', { positive: tab.chartInfo.postMarketChange > 0, negative: tab.chartInfo.postMarketChange < 0 }]">
                {{ tab.chartInfo.postMarketChange > 0 ? '+' : '' }}{{ tab.chartInfo.postMarketChange?.toFixed(2) }}
                ({{ tab.chartInfo.postMarketChangePercent > 0 ? '+' : '' }}{{ tab.chartInfo.postMarketChangePercent?.toFixed(2) }}%)
              </span>
            </template>
            <template v-else-if="tab.chartInfo.preMarketPrice">
              <span class="extended-label">PM</span>
              <span :class="['extended-price', { positive: tab.chartInfo.preMarketChange > 0, negative: tab.chartInfo.preMarketChange < 0 }]">
                {{ tab.chartInfo.preMarketPrice?.toFixed(2) }}
              </span>
              <span :class="['extended-change', { positive: tab.chartInfo.preMarketChange > 0, negative: tab.chartInfo.preMarketChange < 0 }]">
                {{ tab.chartInfo.preMarketChange > 0 ? '+' : '' }}{{ tab.chartInfo.preMarketChange?.toFixed(2) }}
                ({{ tab.chartInfo.preMarketChangePercent > 0 ? '+' : '' }}{{ tab.chartInfo.preMarketChangePercent?.toFixed(2) }}%)
              </span>
            </template>
          </div>

          <!-- OHLC Data -->
          <div class="info-ohlc">
            <div class="ohlc-item">
              <span class="ohlc-label">O</span>
              <span class="ohlc-value">{{ tab.chartInfo.open?.toFixed(2) || '--' }}</span>
            </div>
            <div class="ohlc-item">
              <span class="ohlc-label">H</span>
              <span class="ohlc-value high">{{ tab.chartInfo.high?.toFixed(2) || '--' }}</span>
            </div>
            <div class="ohlc-item">
              <span class="ohlc-label">L</span>
              <span class="ohlc-value low">{{ tab.chartInfo.low?.toFixed(2) || '--' }}</span>
            </div>
            <div class="ohlc-item">
              <span class="ohlc-label">V</span>
              <span class="ohlc-value">{{ formatVolume(tab.chartInfo.volume) }}</span>
            </div>
          </div>
        </div>

        <!-- Chart Toolbar -->
        <div v-if="tab" class="chart-toolbar">
          <div class="timeframe-buttons">
            <button
              v-for="tf in timeframes"
              :key="tf"
              type="button"
              :class="['timeframe-btn', { active: tab.timeframe === tf }]"
              @click.stop="setTimeframe(tab.id, tf)"
            >
              {{ tf }}
            </button>
          </div>
          
          <div class="chart-type-buttons">
            <button
              v-for="type in chartTypes"
              :key="type"
              type="button"
              :class="['chart-type-btn', { active: tab.chartType === type }]"
              @click.stop="setChartType(tab.id, type)"
            >
              {{ type }}
            </button>
          </div>

          <div class="indicators-buttons">
            <button
              type="button"
              :class="['indicator-btn', { active: tab.indicators?.rsi }]"
              @click.stop="toggleIndicator(tab.id, 'rsi')"
              title="RSI (Relative Strength Index)"
            >
              RSI
            </button>
            <button
              type="button"
              :class="['indicator-btn', { active: tab.indicators?.ma13 }]"
              @click.stop="toggleIndicator(tab.id, 'ma13')"
              title="MA 13"
            >
              MA13
            </button>
            <button
              type="button"
              :class="['indicator-btn', { active: tab.indicators?.ma50 }]"
              @click.stop="toggleIndicator(tab.id, 'ma50')"
              title="MA 50"
            >
              MA50
            </button>
            <button
              type="button"
              :class="['indicator-btn', { active: tab.indicators?.ma200 }]"
              @click.stop="toggleIndicator(tab.id, 'ma200')"
              title="MA 200"
            >
              MA200
            </button>
            <button
              type="button"
              :class="['indicator-btn', { active: tab.indicators?.ma800 }]"
              @click.stop="toggleIndicator(tab.id, 'ma800')"
              title="MA 800"
            >
              MA800
            </button>
            <button
              type="button"
              :class="['indicator-btn', { active: tab.indicators?.bullRun }]"
              @click.stop="toggleIndicator(tab.id, 'bullRun')"
              title="Bull/Bear Run Signals"
            >
              🐂🐻
            </button>
          </div>

          <div class="ai-analysis-input">
            <IndicatorSearch
              :loading="tab.aiLoading"
              @analyze="(query) => { tab.aiQuery = query; handleAIAnalysis(tab.id) }"
            />
          </div>

          <div class="toolbar-actions">
            <!-- Settings moved to Profile -->
            <button class="mobile-watchlist-toggle" @click="showWatchlist = !showWatchlist">
              {{ showWatchlist ? 'Close' : 'Watchlist' }}
            </button>
          </div>
        </div>

        <!-- Main Content Area -->
        <div v-if="tab" class="main-content">
          <!-- Left Panel: Watchlist -->
          <div class="left-panel" :class="{ active: showWatchlist }">
            <button class="mobile-close-btn" @click="showWatchlist = false">×</button>
            <div class="search-section">
              <div class="search-input-wrapper">
                <input
                  v-model="searchQuery"
                  @input="handleSearch"
                  @focus="isSearchFocused = true"
                  @blur="isSearchFocused = false"
                  @keyup.enter="addTopResult"
                  @keydown.down.prevent="navigateResults(1)"
                  @keydown.up.prevent="navigateResults(-1)"
                  placeholder="Search stocks, crypto (BTC-USD), futures (CL=F)..."
                  class="search-input"
                  ref="searchInputRef"
                />
                <div class="search-input-glow" :class="{ active: isSearchFocused }"></div>
                <button 
                  @click="addTopResult" 
                  class="add-btn"
                  :disabled="searchResults.length === 0"
                  :title="searchResults.length > 0 ? 'Add first result (Enter)' : 'No results'"
                  :class="{ enabled: searchResults.length > 0 }"
                >
                  <span class="add-icon">✓</span>
                </button>
              </div>
            </div>
            
            <div v-if="searchLoading" class="search-loading">
              <div class="loading-spinner"></div>
              <span>Searching...</span>
            </div>
            
            <div v-else-if="searchQuery.length >= 2 && searchResults.length === 0" class="search-no-results">
              <span class="no-results-icon">🔍</span>
              <p>No results found</p>
              <p class="no-results-hint">Try a different search term</p>
            </div>
            
            <div v-else-if="searchResults.length > 0" class="search-results">
              <div
                v-for="(result, index) in searchResults"
                :key="result.symbol"
                @click.stop="handleResultClick(result, tab.id)"
                @mouseenter="hoveredResultIndex = index"
                @mouseleave="hoveredResultIndex = null"
                @mousedown.prevent
                class="search-result-item"
                :class="{ 
                  hovered: hoveredResultIndex === index,
                  selected: selectedResultIndex === index
                }"
                :title="`${result.symbol} - ${result.name} (${getAssetTypeLabel(result.type)})`"
              >
                <div class="result-main">
                  <div class="result-header">
                    <span class="result-symbol">{{ result.symbol }}</span>
                    <span class="asset-type-badge" :class="getAssetTypeClass(result.type)">
                      {{ getAssetTypeIcon(result.type) }} {{ getAssetTypeLabel(result.type) }}
                    </span>
                  </div>
                  <div class="result-details">
                    <span class="result-name">{{ result.name }}</span>
                    <span v-if="result.exchange && result.exchange !== 'N/A'" class="result-exchange">{{ result.exchange }}</span>
                  </div>
                </div>
                <div class="result-action">
                  <span class="add-hint">Click to add</span>
                </div>
              </div>
            </div>

            <div class="watchlist-sections">
              <div class="watchlist-section watchlist-main">
                <h3 class="panel-title">My Watchlist</h3>
                <div class="watchlist">
                  <div
                    v-for="item in watchlist"
                    :key="item.symbol"
                    :class="['watchlist-item', { active: tab.selectedTicker === item.symbol }]"
                    @click="selectTicker(tab.id, item.symbol)"
                  >
                    <div class="symbol">{{ item.symbol }}</div>
                    <div class="name">{{ item.name }}</div>
                  </div>
                </div>
                <button @click="removeSelected(tab.id)" class="remove-btn">🗑️ Remove</button>
              </div>
              <div class="watchlist-section bot-section">
                <label class="bot-section-header">
                  <input
                    type="checkbox"
                    id="include-bot-ticks"
                    v-model="includeBotTickers"
                    class="bot-tick-checkbox"
                  />
                  <h3 class="panel-title">Bot</h3>
                </label>
                <div v-show="includeBotTickers" class="watchlist bot-watchlist">
                  <div
                    v-for="item in botOrderSymbols"
                    :key="item.symbol"
                    :class="['watchlist-item', { active: tab.selectedTicker === item.symbol }]"
                    @click="selectTicker(tab.id, item.symbol)"
                  >
                    <div class="symbol">{{ item.symbol }}</div>
                    <div class="name">{{ item.name || item.symbol }}</div>
                  </div>
                  <div v-if="botOrderSymbols.length === 0" class="bot-empty">
                    Nessun ordine attivo
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Center: Chart -->
          <div class="chart-container">
            <div
              v-if="!tab.selectedTicker"
              class="welcome-screen"
              @click="focusSearchInput"
              role="button"
              tabindex="0"
              @keydown.enter.prevent="focusSearchInput"
              @keydown.space.prevent="focusSearchInput"
            >
              <h1>Portfolio Tracker</h1>
              <p>Add an asset from the search bar to begin.</p>
              <p class="welcome-screen-hint">Clicca qui o sulla barra di ricerca per aggiungere un titolo</p>
            </div>
            <div v-else class="chart-wrapper" :ref="el => setChartRef(tab.id, el)"
              @contextmenu.prevent="showChartContextMenu($event, tab.id)"
              @click="handleChartClick($event, tab.id)"
              @mousemove="handleChartMouseMove($event, tab.id)"
            ></div>
            
            <!-- Drawing Overlay -->
            <svg v-if="tab.selectedTicker && renderedDrawings[tab.id]" class="drawing-overlay">
              <defs>
                <marker 
                  v-for="drawing in renderedDrawings[tab.id].filter(d => d.type === 'arrow')" 
                  :key="'marker-' + drawing.id"
                  :id="'arrowhead-' + drawing.id" 
                  markerWidth="10" 
                  markerHeight="10" 
                  refX="9" 
                  refY="3" 
                  orient="auto"
                >
                  <polygon points="0 0, 10 3, 0 6" :fill="drawing.color" />
                </marker>
              </defs>
              <g v-for="drawing in renderedDrawings[tab.id]" :key="drawing.id">
                <!-- Line -->
                <line
                  v-if="drawing.type === 'line'"
                  :x1="drawing.x1"
                  :y1="drawing.y1"
                  :x2="drawing.x2"
                  :y2="drawing.y2"
                  :stroke="drawing.color"
                  :stroke-width="drawing.strokeWidth || 2"
                  :class="['drawing-element', { 'temp-drawing': drawing.isTemp, selected: drawing.selected }]"
                  @click.stop="onDrawingClick(tab.id, drawing.id, drawing.isTemp)"
                  @contextmenu.stop.prevent="showChartContextMenu($event, tab.id, drawing.id)"
                />
                <rect
                  v-if="drawing.type === 'square'"
                  :x="Math.min(drawing.x1, drawing.x2)"
                  :y="Math.min(drawing.y1, drawing.y2)"
                  :width="Math.abs(drawing.x2 - drawing.x1)"
                  :height="Math.abs(drawing.y2 - drawing.y1)"
                  :stroke="drawing.color"
                  :stroke-width="drawing.strokeWidth || 2"
                  :fill="drawing.color + '1A'"
                  :class="['drawing-element', { 'temp-drawing': drawing.isTemp, selected: drawing.selected }]"
                  @click.stop="onDrawingClick(tab.id, drawing.id, drawing.isTemp)"
                  @contextmenu.stop.prevent="showChartContextMenu($event, tab.id, drawing.id)"
                />
                <!-- Circle -->
                <ellipse
                  v-if="drawing.type === 'circle'"
                  :cx="(drawing.x1 + drawing.x2) / 2"
                  :cy="(drawing.y1 + drawing.y2) / 2"
                  :rx="Math.abs(drawing.x2 - drawing.x1) / 2"
                  :ry="Math.abs(drawing.y2 - drawing.y1) / 2"
                  :stroke="drawing.color"
                  :stroke-width="drawing.strokeWidth || 2"
                  :fill="drawing.color + '1A'"
                  :class="['drawing-element', { 'temp-drawing': drawing.isTemp, selected: drawing.selected }]"
                  @click.stop="onDrawingClick(tab.id, drawing.id, drawing.isTemp)"
                  @contextmenu.stop.prevent="showChartContextMenu($event, tab.id, drawing.id)"
                />
                <!-- Arrow -->
                <line
                  v-if="drawing.type === 'arrow'"
                  :x1="drawing.x1"
                  :y1="drawing.y1"
                  :x2="drawing.x2"
                  :y2="drawing.y2"
                  :stroke="drawing.color"
                  :stroke-width="drawing.strokeWidth || 2"
                  :marker-end="'url(#arrowhead-' + drawing.id + ')'"
                  :class="['drawing-element', { 'temp-drawing': drawing.isTemp, selected: drawing.selected }]"
                  @click.stop="onDrawingClick(tab.id, drawing.id, drawing.isTemp)"
                  @contextmenu.stop.prevent="showChartContextMenu($event, tab.id, drawing.id)"
                />
                <!-- Horizontal Line -->
                <line
                  v-if="drawing.type === 'hline'"
                  :x1="0"
                  :y1="drawing.y1"
                  :x2="10000"
                  :y2="drawing.y1"
                  :stroke="drawing.color"
                  :stroke-width="drawing.strokeWidth || 2"
                  stroke-dasharray="5,5"
                  :class="['drawing-element', { 'temp-drawing': drawing.isTemp, selected: drawing.selected }]"
                  @click.stop="onDrawingClick(tab.id, drawing.id, drawing.isTemp)"
                  @contextmenu.stop.prevent="showChartContextMenu($event, tab.id, drawing.id)"
                />
                <!-- Vertical Line -->
                <line
                  v-if="drawing.type === 'vline'"
                  :x1="drawing.x1"
                  :y1="0"
                  :x2="drawing.x1"
                  :y2="10000"
                  :stroke="drawing.color"
                  :stroke-width="drawing.strokeWidth || 2"
                  stroke-dasharray="5,5"
                  :class="['drawing-element', { 'temp-drawing': drawing.isTemp, selected: drawing.selected }]"
                  @click.stop="onDrawingClick(tab.id, drawing.id, drawing.isTemp)"
                  @contextmenu.stop.prevent="showChartContextMenu($event, tab.id, drawing.id)"
                />
                <!-- Polygon / Freehand -->
                <polyline
                  v-if="drawing.type === 'polygon' || drawing.type === 'freehand'"
                  :points="drawing.points.map(p => p.x + ',' + p.y).join(' ')"
                  :stroke="drawing.color"
                  :stroke-width="drawing.strokeWidth || 2"
                  fill="none"
                  :class="['drawing-element', { 'temp-drawing': drawing.isTemp, selected: drawing.selected }]"
                  @click.stop="onDrawingClick(tab.id, drawing.id, drawing.isTemp)"
                  @contextmenu.stop.prevent="showChartContextMenu($event, tab.id, drawing.id)"
                />
                <!-- Triangle -->
                <polygon
                  v-if="drawing.type === 'triangle'"
                  :points="drawing.points.map(p => p.x + ',' + p.y).join(' ')"
                  :stroke="drawing.color"
                  :stroke-width="drawing.strokeWidth || 2"
                  :fill="drawing.color + '1A'"
                  :class="['drawing-element', { 'temp-drawing': drawing.isTemp, selected: drawing.selected }]"
                  @click.stop="onDrawingClick(tab.id, drawing.id, drawing.isTemp)"
                  @contextmenu.stop.prevent="showChartContextMenu($event, tab.id, drawing.id)"
                />
                <!-- Text -->
                <text
                  v-if="drawing.type === 'text'"
                  :x="drawing.x1"
                  :y="drawing.y1"
                  :fill="drawing.color"
                  :font-size="drawing.fontSize || 14"
                  font-weight="600"
                  :class="['drawing-element', { 'temp-drawing': drawing.isTemp, selected: drawing.selected }]"
                  @click.stop="onDrawingClick(tab.id, drawing.id, drawing.isTemp)"
                  @dblclick.stop="drawing.type === 'text' && !drawing.isTemp && (selectDrawing(tab.id, drawing.id), openEditTextForSelected())"
                  @contextmenu.stop.prevent="showChartContextMenu($event, tab.id, drawing.id)"
                >
                  {{ drawing.text }}
                </text>
              </g>
            </svg>

            <!-- Floating Tool Palette (inside chart, constrained to bounds) -->
            <FloatingToolPalette
              v-if="tab.selectedTicker"
              :current-tool="drawingMode"
              v-model:color="selectedColor"
              @set-tool="startDrawing"
              @undo="undoLastDrawing(tab.id)"
              @clear-all="clearAllDrawings(tab.id)"
              @ai-draw="openAiDrawModal"
            />

            <!-- Drawing Properties Panel (when a drawing is selected) -->
            <div
              v-if="tab.selectedTicker && selectedDrawing.tabId === tab.id && selectedDrawing.drawingId && getSelectedDrawingRaw()"
              class="drawing-properties-panel"
              @mousedown.stop
            >
              <div class="drawing-properties-header">
                <span>Proprietà disegno</span>
                <button type="button" class="drawing-props-close" @click="deselectDrawing" title="Chiudi">×</button>
              </div>
              <div class="drawing-properties-body">
                <div class="drawing-prop-row">
                  <label>Colore</label>
                  <input
                    type="color"
                    :value="getSelectedDrawingRaw()?.color || '#2196F3'"
                    @input="updateSelectedDrawing({ color: $event.target.value })"
                    class="drawing-color-input"
                  />
                </div>
                <div v-if="getSelectedDrawingRaw()?.type !== 'text'" class="drawing-prop-row">
                  <label>Spessore ({{ getSelectedDrawingRaw()?.strokeWidth || 2 }})</label>
                  <input
                    type="range"
                    min="1"
                    max="6"
                    :value="getSelectedDrawingRaw()?.strokeWidth ?? 2"
                    @input="updateSelectedDrawing({ strokeWidth: parseInt($event.target.value, 10) })"
                    class="drawing-thickness-slider"
                  />
                </div>
                <div v-if="getSelectedDrawingRaw()?.type === 'text'" class="drawing-prop-row">
                  <label>Dimensione testo ({{ getSelectedDrawingRaw()?.fontSize || 14 }})</label>
                  <input
                    type="range"
                    min="10"
                    max="28"
                    :value="getSelectedDrawingRaw()?.fontSize ?? 14"
                    @input="updateSelectedDrawing({ fontSize: parseInt($event.target.value, 10) })"
                    class="drawing-thickness-slider"
                  />
                </div>
                <div v-if="getSelectedDrawingRaw()?.type === 'text'" class="drawing-prop-row">
                  <label>Testo</label>
                  <div class="drawing-text-edit">
                    <input
                      type="text"
                      :value="getSelectedDrawingRaw()?.text || ''"
                      @input="updateSelectedDrawing({ text: $event.target.value })"
                      class="drawing-text-input"
                      placeholder="Testo"
                    />
                    <button type="button" class="drawing-edit-btn" @click="openEditTextForSelected" title="Modifica testo (finestra)">✎</button>
                  </div>
                </div>
                <div class="drawing-prop-actions">
                  <button type="button" class="drawing-delete-btn" @click="removeDrawing(selectedDrawing.tabId, selectedDrawing.drawingId); deselectDrawing()">
                    Elimina
                  </button>
                </div>
              </div>
            </div>
          </div>

        </div>
      </div>
      </template>
    </div>

    <!-- Settings Modal Removed (Redundant) -->

    <!-- Profile Modal -->
    <ProfileModal
      :show="showProfileModal"
      :user="currentUser"
      @close="showProfileModal = false"
      @saved="handleProfileSaved"
    />

    <!-- AI Draw Modal -->
    <AiDrawModal
      v-if="showAiDrawModal"
      :chart-data="getCurrentChartData()"
      :selected-color="selectedColor"
      @close="showAiDrawModal = false"
      @drawing-added="handleAiDrawingAdded"
    />
    
    <!-- Tab Wizard -->
    <TabWizard
      :show="showTabWizard"
      @close="showTabWizard = false"
      @create="handleCreateTab"
    />

    <!-- Share Live Modal -->
    <div v-if="showShareModal" class="modal-overlay" @click="closeShareModal">
      <div class="modal-content share-modal" @click.stop>
        <div class="modal-header">
          <h3>Condividi una tab live</h3>
          <button class="close-btn" @click="closeShareModal">×</button>
        </div>
        <div class="modal-body">
          <p class="share-hint">Seleziona la tab da condividere. La condivisione appare in chat pubblica.</p>
          <div v-if="!shareableTabs.length" class="share-empty">
            Nessuna tab condivisibile disponibile.
          </div>
          <div v-else class="share-list">
            <button
              v-for="tab in shareableTabs"
              :key="tab.id"
              class="share-item"
              :class="{ selected: selectedShareTabId === tab.id }"
              @click="selectedShareTabId = tab.id"
            >
              <div class="share-item-title">{{ tab.name }}</div>
              <div class="share-item-type">{{ tab.type }}</div>
            </button>
          </div>
          <div v-if="shareError" class="share-error">{{ shareError }}</div>
        </div>
        <div class="modal-footer">
          <button class="tab-share-btn ghost" @click="closeShareModal">Annulla</button>
          <button class="tab-share-btn primary" :disabled="!selectedShareTabId || shareLoading" @click="shareSelectedTab">
            {{ shareLoading ? '...' : 'Condividi' }}
          </button>
        </div>
      </div>
    </div>
    
    <!-- Backdrop per chiudere i menu contestuali cliccando fuori -->
    <div
      v-if="contextMenu.show || (chartContextMenu.show && chartContextMenu.drawingId)"
      class="context-menu-backdrop"
      @click="closeContextMenu(); closeChartContextMenu()"
    ></div>

    <!-- Tab Context Menu -->
    <div
      v-if="contextMenu.show"
      class="context-menu"
      :style="{ left: contextMenu.x + 'px', top: contextMenu.y + 'px' }"
      @click.stop
    >
      <button @click="startRenameTab(contextMenu.tab)" class="context-menu-item">
        Rename
      </button>
      <button
        @click="removeTab(contextMenu.tab.id)"
        class="context-menu-item"
        type="button"
      >
        Remove
      </button>
    </div>

    <!-- Chart Context Menu (Only for existing drawings) -->
    <div
      v-if="chartContextMenu.show && chartContextMenu.drawingId"
      class="context-menu"
      :style="{ left: chartContextMenu.x + 'px', top: chartContextMenu.y + 'px' }"
      @click.stop
    >
      <button @click="selectDrawing(chartContextMenu.tabId, chartContextMenu.drawingId); closeChartContextMenu()" class="context-menu-item">
        Modifica proprietà
      </button>
      <button @click="removeDrawing(chartContextMenu.tabId, chartContextMenu.drawingId)" class="context-menu-item delete">
        Elimina disegno
      </button>
    </div>

  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { createChart } from 'lightweight-charts'
import { useWatchlistStore } from '../stores/watchlist'
import { useNewsStore } from '../stores/news'
import { useAuthStore } from '../stores/auth'

import NewsFeed from '../components/NewsFeed.vue'
import BotList from '../components/BotList.vue'
import FlexChat from '../components/FlexChat.vue'
import EarningsList from '../components/EarningsList.vue'
import UserProfile from '../components/UserProfile.vue'
import LoginModal from '../components/LoginModal.vue'
import RegisterModal from '../components/RegisterModal.vue'
import ProfileModal from '../components/ProfileModal.vue'
import StrategyBuilder from '../components/StrategyBuilder.vue'
import BacktestingPanel from '../components/BacktestingPanel.vue'

import TabWizard from '../components/TabWizard.vue'
import IndicatorSearch from '../components/IndicatorSearch.vue'
import AiDrawModal from '../components/AiDrawModal.vue'
import FloatingToolPalette from '../components/FloatingToolPalette.vue'
import api from '../services/api'
import { getCached, setCached, saveIndicatorSettings, loadIndicatorSettings } from '../utils/cache'
import { getWsBase } from '@/utils/env'

const watchlistStore = useWatchlistStore()
const newsStore = useNewsStore()
const authStore = useAuthStore()

const timeframes = ['1d', '5d', '1m', '3m', '6m', '1y', '5y', 'MAX']
const chartTypes = ['Candle', 'Line']

// Non inizializzare activeTab da localStorage subito - verrà impostato dopo il caricamento dei tab
const activeTab = ref(null)
const tabsLoaded = ref(false) // Flag per sapere quando i tab sono stati caricati
const tabs = ref([
  {
    id: 1,
    name: 'Stocks',
    type: 'stocks',
    selectedTicker: null,
    timeframe: '1y',
    chartType: 'Candle',
    chartInfo: {
      symbol: '',
      name: '',
      price: null,
      change: null,
      changePercent: null,
      volume: null
    },
    chart: null,
    candlestickSeries: null,
    lineSeries: null,
    aiQuery: '',
    aiLoading: false,
    aiIndicators: [],
    drawings: []
  },

  {
    id: 3,
    name: 'News',
    type: 'news'
  },
  {
    id: 4,
    name: 'Bot',
    type: 'bot'
  },
  {
    id: 5,
    name: 'Chat',
    type: 'chat',
    chatConfig: {
      recipientId: null,
      inviteAi: false
    }
  }
])

const searchQuery = ref('')
const searchResults = ref([])
const showAiDrawModal = ref(false)
const showRegisterModal = ref(false)
const showProfileModal = ref(false)
const showTabWizard = ref(false)
const chartRefs = ref({})
const editingTab = ref(null)
const editingTabName = ref('')
const contextMenu = ref({ show: false, x: 0, y: 0, tab: null })
const chartContextMenu = ref({ show: false, x: 0, y: 0, tabId: null, drawingId: null })
const sharedWs = ref(null)
const sharedWsConnected = ref(false)
let sharedWsRetryTimer = null
const sharedSessions = ref({})
const sharedUpdateLocks = new Set()
const showShareModal = ref(false)
const selectedShareTabId = ref(null)
const shareLoading = ref(false)
const shareError = ref('')
const showWatchlist = ref(false) // New state for mobile watchlist drawer
const leftPanelCollapsed = ref(false) // Collapsed state for desktop left panel
const loadingMoreData = ref({}) // Track which tabs are loading more historical data
const drawingMode = ref(null) // null, 'line', 'square', 'circle', 'arrow', 'hline', 'vline', 'text', 'triangle', 'polygon', 'freehand'
const drawingStart = ref(null) // { time, price }
const tempDrawing = ref(null) // { type, points: [], color, text }
const renderedDrawings = ref({}) // Map tabId -> array of { id, type, points, color, text, isTemp }
const selectedDrawing = ref({ tabId: null, drawingId: null }) // Currently selected drawing for editing
const selectedColor = ref('#2196F3') // Default blue
const showColorPicker = ref(false)
const draggedTabId = ref(null)
const draggedTabIndex = ref(null)
const dragOverIndex = ref(null)
const searchTimeout = ref(null)
const searchLoading = ref(false)
const searchError = ref(null)
const isAddingToWatchlist = ref(false)
const isSearchFocused = ref(false)
const hoveredResultIndex = ref(null)
const selectedResultIndex = ref(null)
const searchInputRef = ref(null)
const currentUser = computed(() => authStore.user)
const isLoggedIn = computed(() => authStore.isAuthenticated)
const shareableTabs = computed(() => {
  return tabs.value
    .filter(t => t && ['stocks', 'strategy', 'backtesting'].includes(t.type))
    .map(t => ({ id: t.id, name: t.name, type: t.type }))
})
const botOrderSymbols = ref([])
const includeBotTickers = ref(true)
let botOrdersInterval = null
let chartInfoInterval = null
let chartDataInterval = null

const watchlist = computed(() => watchlistStore.watchlist)
const newsItems = computed(() => newsStore.news)

const setChartRef = (tabId, el) => {
  if (el) {
    chartRefs.value[tabId] = el
  }
}

const loadBotOrders = async () => {
  if (!isLoggedIn.value) return
  try {
    const res = await api.getBotDecisions(100, null)
    const decisions = res.data?.decisions ?? []
    const pending = decisions.filter(d => d.status === 'PENDING' && d.symbol)
    const seen = new Set()
    const wlMap = Object.fromEntries(watchlist.value.map(w => [w.symbol, w.name]))
    const symbols = []
    for (const d of pending) {
      if (!seen.has(d.symbol)) {
        seen.add(d.symbol)
        symbols.push({ symbol: d.symbol, name: wlMap[d.symbol] || d.symbol })
      }
    }
    botOrderSymbols.value = symbols
  } catch (e) {
    botOrderSymbols.value = []
  }
}

onMounted(async () => {
  // Check authentication
  await authStore.checkAuth()
  
  // Load user tabs if authenticated
  if (isLoggedIn.value) {
    await loadUserTabs()
    await loadBotOrders()
    botOrdersInterval = setInterval(loadBotOrders, 60000) // refresh every 60s
  } else {
    // Se non loggato, imposta il tab attivo dai default
    const savedTabId = parseInt(localStorage.getItem('activeTab'))
    const savedTabExists = tabs.value.some(tab => tab.id === savedTabId)
    activeTab.value = savedTabExists ? savedTabId : (tabs.value.length > 0 ? tabs.value[0].id : 1)
    tabsLoaded.value = true
  }
  
  await watchlistStore.loadWatchlist()
  await newsStore.loadNews()
  if (watchlist.value.length > 0) {
    const firstTab = tabs.value.find(t => t.type === 'stocks')
    if (firstTab) {
      selectTicker(firstTab.id, watchlist.value[0].symbol)
    }
  }
  
  // Close context menu when clicking outside
  document.addEventListener('click', closeContextMenu)
  document.addEventListener('keydown', handleKeyDown)
})
onUnmounted(() => {
  if (botOrdersInterval) clearInterval(botOrdersInterval)
  stopChartRefresh()
  document.removeEventListener('click', closeContextMenu)
  document.removeEventListener('keydown', handleKeyDown)
  if (sharedWs.value) {
    sharedWs.value.close()
    sharedWs.value = null
  }
})

watch(isLoggedIn, (val) => {
  if (val) {
    loadBotOrders()
    if (botOrdersInterval) clearInterval(botOrdersInterval)
    botOrdersInterval = setInterval(loadBotOrders, 60000)
  } else {
    if (botOrdersInterval) {
      clearInterval(botOrdersInterval)
      botOrdersInterval = null
    }
    botOrderSymbols.value = []
    if (sharedWs.value) {
      sharedWs.value.close()
      sharedWs.value = null
    }
    sharedWsConnected.value = false
  }
})

const stopChartRefresh = () => {
  if (chartInfoInterval) {
    clearInterval(chartInfoInterval)
    chartInfoInterval = null
  }
  if (chartDataInterval) {
    clearInterval(chartDataInterval)
    chartDataInterval = null
  }
}

const startChartRefresh = (tabId) => {
  stopChartRefresh()
  // Update price/quote in the info bar every 30s so the number moves
  chartInfoInterval = setInterval(() => {
    if (activeTab.value === tabId) updateChartInfo(tabId)
  }, 30000)
  // Refetch chart data every 60s so candlesticks update (last bar / new bars)
  chartDataInterval = setInterval(() => {
    if (activeTab.value === tabId) loadChart(tabId, true)
  }, 60000)
}

const setActiveTab = (tabId) => {
  activeTab.value = tabId
  // Persist active tab to localStorage
  localStorage.setItem('activeTab', tabId.toString())
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab && tab.selectedTicker && tab.type === 'stocks') {
    nextTick(() => {
      loadChart(tabId)
      startChartRefresh(tabId)
    })
  } else {
    stopChartRefresh()
  }
  closeContextMenu()
  closeChartContextMenu()
  deselectDrawing()
  showWatchlist.value = false // Close watchlist on mobile when switching tabs
}

const getSharedParticipantsCount = (shareId) => {
  return sharedSessions.value?.[shareId]?.participants?.length || 1
}

const openShareModal = () => {
  shareError.value = ''
  selectedShareTabId.value = null
  showShareModal.value = true
}

const closeShareModal = () => {
  showShareModal.value = false
  shareError.value = ''
}

const shareSelectedTab = async () => {
  if (!selectedShareTabId.value) return
  if (!authStore.isAuthenticated) {
    shareError.value = 'Accedi per condividere una tab.'
    return
  }
  shareLoading.value = true
  shareError.value = ''
  try {
    const snapshot = getTabSnapshot(selectedShareTabId.value)
    if (!snapshot?.tab_type || !snapshot?.tab_name) {
      shareError.value = 'Impossibile condividere questa tab.'
      shareLoading.value = false
      return
    }
    const { data } = await api.createSharedTab({
      tab_type: snapshot.tab_type,
      tab_name: snapshot.tab_name,
      tab_state: snapshot.tab_state || {}
    })
    const shared = data?.shared_tab
    const sharePayload = {
      share_id: data?.share_id,
      tab_type: snapshot.tab_type,
      tab_name: snapshot.tab_name,
      owner_id: currentUser.value?.id,
      owner_username: currentUser.value?.username,
      created_at: shared?.created_at
    }
    await api.sendChatMessage({
      message: JSON.stringify(sharePayload),
      type: 'tab_share',
      recipient_id: null
    })
    handleShareStarted({
      share_id: sharePayload.share_id,
      tab_id: snapshot.tab_id,
      tab_type: snapshot.tab_type,
      tab_name: snapshot.tab_name,
      tab_state: snapshot.tab_state || {}
    })
    showShareModal.value = false

    const chatTab = tabs.value.find(t => t.type === 'chat' || t.type === 'flex')
    if (chatTab) {
      activeTab.value = chatTab.id
    }
  } catch (error) {
    console.error('Error sharing tab:', error)
    shareError.value = error.response?.data?.detail || error.message
  } finally {
    shareLoading.value = false
  }
}

const connectSharedWebSocket = () => {
  if (sharedWs.value && (sharedWs.value.readyState === WebSocket.CONNECTING || sharedWs.value.readyState === WebSocket.OPEN)) {
    return
  }
  const wsUrl = `${getWsBase()}?token=${authStore.token || ''}`
  sharedWs.value = new WebSocket(wsUrl)

  sharedWs.value.onopen = () => {
    sharedWsConnected.value = true
  }

  sharedWs.value.onmessage = async (event) => {
    try {
      const message = JSON.parse(event.data)
      if (message.type === 'tab_update') {
        await applySharedTabPatch(message.share_id, message.patch, message.sender_id)
      } else if (message.type === 'tab_stopped') {
        handleSharedTabStopped(message.share_id)
      } else if (message.type === 'tab_joined' || message.type === 'tab_left') {
        const shareId = message.share_id
        if (!shareId) return
        if (!sharedSessions.value[shareId]) return
        sharedSessions.value[shareId].participants = message.participants || []
      }
    } catch (e) {
      console.error('Shared WS error:', e)
    }
  }

  sharedWs.value.onerror = (err) => {
    console.warn('Shared WebSocket error:', err)
    sharedWsConnected.value = false
  }

  sharedWs.value.onclose = () => {
    sharedWsConnected.value = false
    if (sharedWsRetryTimer) return
    sharedWsRetryTimer = setTimeout(() => {
      sharedWsRetryTimer = null
      connectSharedWebSocket()
    }, 3000)
  }
}

const sendSharedWs = (payload) => {
  if (!payload) return
  if (!sharedWs.value || sharedWs.value.readyState !== WebSocket.OPEN) {
    connectSharedWebSocket()
    setTimeout(() => {
      if (sharedWs.value && sharedWs.value.readyState === WebSocket.OPEN) {
        sharedWs.value.send(JSON.stringify(payload))
      }
    }, 300)
    return
  }
  sharedWs.value.send(JSON.stringify(payload))
}

const withSharedUpdateLock = async (tabId, fn) => {
  sharedUpdateLocks.add(tabId)
  try {
    await fn()
  } finally {
    sharedUpdateLocks.delete(tabId)
  }
}

const isSharedLocked = (tabId) => sharedUpdateLocks.has(tabId)

const broadcastSharedPatch = (tabId, patch) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab?.sharedSession?.share_id) return
  if (isSharedLocked(tabId)) return
  sendSharedWs({
    type: 'tab_update',
    share_id: tab.sharedSession.share_id,
    patch: patch || {}
  })
}

const handleSharedTabStopped = (shareId) => {
  const session = sharedSessions.value[shareId]
  if (!session) return
  const tab = tabs.value.find(t => t && t.id === session.tabId)
  if (tab) {
    tab.sharedSession = null
  }
  delete sharedSessions.value[shareId]
}

const applySharedTabPatch = async (shareId, patch, senderId) => {
  if (!shareId || !patch) return
  if (senderId && senderId === currentUser.value?.id) return
  const session = sharedSessions.value[shareId]
  if (!session) return
  const tab = tabs.value.find(t => t && t.id === session.tabId)
  if (!tab) return
  await withSharedUpdateLock(tab.id, async () => {
    if (tab.type === 'stocks') {
      if (patch.selectedTicker) {
        await selectTicker(tab.id, patch.selectedTicker)
      }
      if (patch.timeframe && patch.timeframe !== tab.timeframe) {
        tab.timeframe = patch.timeframe
        await loadChart(tab.id)
      }
      if (patch.chartType && patch.chartType !== tab.chartType) {
        tab.chartType = patch.chartType
        await loadChart(tab.id)
      }
      if (patch.indicators) {
        tab.indicators = patch.indicators
        if (tab.selectedTicker) {
          saveIndicatorSettings(tab.selectedTicker, tab.indicators)
          await loadChart(tab.id)
        }
      }
      if (patch.drawings) {
        tab.drawings = patch.drawings
        updateDrawingCoordinates(tab.id)
      }
    } else if (tab.type === 'strategy' && patch.strategyState) {
      tab.strategyState = patch.strategyState
    } else if (tab.type === 'backtesting' && patch.backtestingState) {
      tab.backtestingState = patch.backtestingState
    }
  })
}

const getTabSnapshot = (tabId) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab) return null
  if (tab.type === 'stocks') {
    return {
      tab_id: tab.id,
      tab_type: tab.type,
      tab_name: tab.name,
      tab_state: {
        selectedTicker: tab.selectedTicker,
        timeframe: tab.timeframe,
        chartType: tab.chartType,
        indicators: tab.indicators || null,
        drawings: tab.drawings || []
      }
    }
  }
  if (tab.type === 'strategy') {
    return {
      tab_id: tab.id,
      tab_type: tab.type,
      tab_name: tab.name,
      tab_state: {
        strategyState: tab.strategyState || null
      }
    }
  }
  if (tab.type === 'backtesting') {
    return {
      tab_id: tab.id,
      tab_type: tab.type,
      tab_name: tab.name,
      tab_state: {
        backtestingState: tab.backtestingState || null
      }
    }
  }
  return null
}

const handleShareStarted = (payload) => {
  const tab = tabs.value.find(t => t && t.id === payload.tab_id)
  if (!tab || !payload.share_id) return
  tab.sharedSession = {
    share_id: payload.share_id,
    isOwner: true,
    tab_name: payload.tab_name,
    active: true
  }
  sharedSessions.value[payload.share_id] = {
    tabId: tab.id,
    participants: [currentUser.value?.id].filter(Boolean),
    ownerId: currentUser.value?.id,
    ownerUsername: currentUser.value?.username,
    active: true
  }
  connectSharedWebSocket()
  sendSharedWs({ type: 'tab_join', share_id: payload.share_id })
}

const handleOpenSharedTab = async (payload) => {
  const shareId = payload?.share_id
  if (!shareId) return
  const existing = tabs.value.find(t => t?.sharedSession?.share_id === shareId)
  if (existing) {
    activeTab.value = existing.id
    return
  }
  try {
    const { data } = await api.getSharedTab(shareId)
    const shared = data?.shared_tab
    if (!shared) return
    const newId = tabs.value.length > 0 ? Math.max(...tabs.value.map(t => t.id)) + 1 : 1
    const tabState = shared.tab_state || {}
    const newTab = {
      id: newId,
      name: shared.tab_name || 'Shared Tab',
      type: shared.tab_type,
      chart: null,
      candlestickSeries: null,
      lineSeries: null,
      earningsLines: [],
      drawings: tabState.drawings || [],
      selectedTicker: tabState.selectedTicker || null,
      timeframe: tabState.timeframe || '1y',
      chartType: tabState.chartType || 'Candle',
      indicators: tabState.indicators || null,
      chartInfo: {
        symbol: tabState.selectedTicker || '',
        name: '',
        price: null,
        change: null,
        changePercent: null,
        volume: null
      },
      strategyState: tabState.strategyState || null,
      backtestingState: tabState.backtestingState || null,
      sharedSession: {
        share_id: shareId,
        isOwner: shared.owner_id === currentUser.value?.id,
        tab_name: shared.tab_name,
        active: true
      }
    }
    tabs.value.push(newTab)
    activeTab.value = newId
    sharedSessions.value[shareId] = {
      tabId: newId,
      participants: shared.participants || [],
      ownerId: shared.owner_id,
      ownerUsername: shared.owner_username,
      active: true
    }
    connectSharedWebSocket()
    sendSharedWs({ type: 'tab_join', share_id: shareId })
    if (newTab.type === 'stocks' && newTab.selectedTicker) {
      await nextTick()
      await withSharedUpdateLock(newId, async () => {
        await selectTicker(newId, newTab.selectedTicker)
      })
    }
  } catch (error) {
    console.error('Error opening shared tab:', error)
    alert('Impossibile aprire la tab condivisa.')
  }
}

const stopSharingTab = async (tabId) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  const shareId = tab?.sharedSession?.share_id
  if (!shareId) return
  try {
    await api.stopSharedTab(shareId)
  } catch (error) {
    console.error('Error stopping share:', error)
  } finally {
    tab.sharedSession = null
    delete sharedSessions.value[shareId]
  }
}

const handleStrategyStateChange = (tabId, state) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab) return
  tab.strategyState = state
  broadcastSharedPatch(tabId, { strategyState: state })
}

const handleBacktestingStateChange = (tabId, state) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab) return
  tab.backtestingState = state
  broadcastSharedPatch(tabId, { backtestingState: state })
}

const loadUserTabs = async () => {
  try {
    const response = await api.getUserTabs()
    
    // Salva il tab attivo corrente PRIMA di sostituire l'array
    const currentActiveTab = activeTab.value
    
    if (response.data && response.data.tabs && response.data.tabs.length > 0) {
      // Restore tabs from user account - usa nextTick per evitare flash
      const newTabs = response.data.tabs.map(tab => ({
        ...tab,
        chart: null,
        candlestickSeries: null,
        lineSeries: null,
        earningsLines: tab.earningsLines || [],
        drawings: tab.drawings || [],
        sharedSession: null,
        strategyState: tab.strategyState || null,
        backtestingState: tab.backtestingState || null
      }))
      
      // Sostituisci l'array in un colpo solo per evitare re-render intermedi
      tabs.value = newTabs
    } else {
      // First time user - save default tabs to account
      const defaultTabs = tabs.value.map(tab => {
        const { chart, candlestickSeries, lineSeries, resizeObserver, ...tabData } = tab
        return tabData
      })
      await api.saveUserTabs(defaultTabs)
    }
    
    // Dopo aver caricato i tab, imposta il tab attivo
    // Verifica che il tab salvato in localStorage esista ancora
    const savedTabId = currentActiveTab || parseInt(localStorage.getItem('activeTab'))
    const savedTabExists = tabs.value.some(tab => tab.id === savedTabId)
    
    // Usa nextTick per assicurarsi che Vue abbia aggiornato il DOM prima di cambiare activeTab
    await nextTick()
    
    if (savedTabExists) {
      activeTab.value = savedTabId
    } else if (tabs.value.length > 0) {
      // Se il tab salvato non esiste più, usa il primo tab disponibile
      activeTab.value = tabs.value[0].id
      localStorage.setItem('activeTab', activeTab.value.toString())
    }
    
    // Imposta tabsLoaded solo dopo aver impostato activeTab
    await nextTick()
    tabsLoaded.value = true
  } catch (error) {
    console.error('Error loading user tabs:', error)
    // If error loading, keep default tabs
    // Imposta comunque il tab attivo dai default
    const savedTabId = parseInt(localStorage.getItem('activeTab'))
    const savedTabExists = tabs.value.some(tab => tab.id === savedTabId)
    activeTab.value = savedTabExists ? savedTabId : (tabs.value.length > 0 ? tabs.value[0].id : 1)
    
    await nextTick()
    tabsLoaded.value = true
  }
}

const saveUserTabs = async () => {
  if (!isLoggedIn.value) return
  
  try {
    // Remove chart references before saving
    const tabsToSave = tabs.value.map(tab => {
      const { chart, candlestickSeries, lineSeries, resizeObserver, sharedSession, ...tabData } = tab
      return tabData
    })
    await api.saveUserTabs(tabsToSave)
  } catch (error) {
    console.error('Error saving user tabs:', error)
  }
}

const handleCreateTab = (tabConfig) => {
  const newId = tabs.value.length > 0 ? Math.max(...tabs.value.map(t => t.id)) + 1 : 1
  const newTab = {
    id: newId,
    ...tabConfig,
    chart: null,
    candlestickSeries: null,
    lineSeries: null,
    earningsLines: [],
    drawings: [],
    sharedSession: null,
    strategyState: null,
    backtestingState: null
  }
  tabs.value.push(newTab)
  activeTab.value = newId
  saveUserTabs()
}

const startRenameTab = (tab) => {
  closeContextMenu()
  editingTab.value = tab
  editingTabName.value = tab.name
}

const finishRenameTab = () => {
  if (editingTab.value && editingTabName.value.trim()) {
    editingTab.value.name = editingTabName.value.trim()
    saveUserTabs()
  }
  editingTab.value = null
  editingTabName.value = ''
}

const cancelRenameTab = () => {
  editingTab.value = null
  editingTabName.value = ''
}

const removeTab = (tabId) => {
  // Use loose equality to handle potential string/number mismatches
  const index = tabs.value.findIndex(t => t.id == tabId)
  if (index === -1) {
    console.error('Tab not found for removal:', tabId)
    closeContextMenu()
    return
  }
  
  const tab = tabs.value[index]
  
  closeContextMenu()
  
  // Confirm before removing
  if (!confirm(`Are you sure you want to remove the tab "${tab.name}"?`)) {
    return
  }

  if (tab.sharedSession?.share_id) {
    if (tab.sharedSession.isOwner) {
      stopSharingTab(tabId)
    } else {
      sendSharedWs({ type: 'tab_leave', share_id: tab.sharedSession.share_id })
      delete sharedSessions.value[tab.sharedSession.share_id]
    }
  }
  
  // Clean up chart if it exists
  if (tab.chart) {
    try {
      if (tab.earningsLines && tab.earningsLines.length > 0) {
        tab.earningsLines.forEach(line => {
          try {
            tab.chart.removeSeries(line)
          } catch (e) {
            // Series might already be removed
          }
        })
      }
      tab.chart.remove()
    } catch (e) {
      console.error('Error removing chart:', e)
    }
  }
  
  tabs.value.splice(index, 1)
  
  // If removed tab was active, switch to another tab
  if (activeTab.value === tabId) {
    if (tabs.value.length > 0) {
      activeTab.value = tabs.value[Math.max(0, index - 1)].id
    } else {
      // If no tabs left, create a default one
      handleCreateTab({
        name: 'Stocks',
        type: 'stocks',
        selectedTicker: null,
        timeframe: '1y',
        chartType: 'Candle',
        chartInfo: {
          symbol: '',
          name: '',
          price: null,
          change: null,
          changePercent: null,
          volume: null
        }
      })
    }
  }
  
  saveUserTabs()
  closeContextMenu()
  closeChartContextMenu()
}

const showTabContextMenu = (event, tab) => {
  contextMenu.value = {
    show: true,
    x: event.clientX,
    y: event.clientY,
    tab: tab
  }
}

const closeContextMenu = () => {
  contextMenu.value.show = false
  chartContextMenu.value.show = false
}

const closeChartContextMenu = () => {
  chartContextMenu.value.show = false
}

const showChartContextMenu = (event, tabId, drawingId = null) => {
  event.preventDefault()
  
  // Only show context menu if clicking on an existing drawing (to delete it)
  if (!drawingId) return

  // Calculate position to keep menu on screen
  const menuWidth = 220 
  const menuHeight = 60
  
  let x = event.clientX
  let y = event.clientY
  
  // Adjust horizontal
  if (x + menuWidth > window.innerWidth) {
    x = window.innerWidth - menuWidth - 10
  }
  
  // Adjust vertical
  if (y + menuHeight > window.innerHeight) {
    y = window.innerHeight - menuHeight - 10
  }
  
  chartContextMenu.value = {
    show: true,
    x: x,
    y: y,
    tabId: tabId,
    drawingId: drawingId
  }
}

const undoLastDrawing = (tabId) => {
  const tab = tabs.value.find(t => t.id === tabId)
  if (tab && tab.drawings && tab.drawings.length > 0) {
    tab.drawings.pop()
    saveUserTabs()
    updateDrawingCoordinates(tabId)
    broadcastSharedPatch(tabId, { drawings: tab.drawings })
  }
  closeChartContextMenu()
}

const clearAllDrawings = (tabId) => {
  const tab = tabs.value.find(t => t.id === tabId)
  if (tab && tab.drawings && tab.drawings.length > 0) {
    if (confirm('Are you sure you want to clear all drawings?')) {
      tab.drawings = []
      saveUserTabs()
      updateDrawingCoordinates(tabId)
      broadcastSharedPatch(tabId, { drawings: tab.drawings })
    }
  }
  closeChartContextMenu()
}

const selectDrawing = (tabId, drawingId) => {
  selectedDrawing.value = { tabId, drawingId }
}

const deselectDrawing = () => {
  selectedDrawing.value = { tabId: null, drawingId: null }
}

const getSelectedDrawingRaw = () => {
  const { tabId, drawingId } = selectedDrawing.value
  if (!tabId || !drawingId) return null
  const tab = tabs.value.find(t => t.id === tabId)
  if (!tab || !tab.drawings) return null
  return tab.drawings.find(d => d.id === drawingId) || null
}

const updateSelectedDrawing = (updates) => {
  const raw = getSelectedDrawingRaw()
  if (!raw) return
  Object.assign(raw, updates)
  saveUserTabs()
  if (selectedDrawing.value.tabId) {
    updateDrawingCoordinates(selectedDrawing.value.tabId)
    broadcastSharedPatch(selectedDrawing.value.tabId, { drawings: tabs.value.find(t => t.id === selectedDrawing.value.tabId)?.drawings || [] })
  }
}

const openEditTextForSelected = () => {
  const raw = getSelectedDrawingRaw()
  if (!raw || raw.type !== 'text') return
  const newText = prompt('Modifica testo:', raw.text || '')
  if (newText !== null) {
    updateSelectedDrawing({ text: newText })
  }
}

const startDrawing = (type) => {
  drawingMode.value = type
  closeChartContextMenu()
  deselectDrawing()
  
  // For text, prompt immediately
  if (type === 'text') {
    const text = prompt('Enter text:')
    if (!text) {
      drawingMode.value = null
      return
    }
    tempDrawing.value = { type: 'text', text, color: selectedColor.value }
  }
}

const removeDrawing = (tabId, drawingId) => {
  const tab = tabs.value.find(t => t.id === tabId)
  if (tab && tab.drawings) {
    const index = tab.drawings.findIndex(d => d.id === drawingId)
    if (index !== -1) {
      tab.drawings.splice(index, 1)
      saveUserTabs()
      updateDrawingCoordinates(tabId)
      broadcastSharedPatch(tabId, { drawings: tab.drawings })
      if (selectedDrawing.value.tabId === tabId && selectedDrawing.value.drawingId === drawingId) {
        deselectDrawing()
      }
    }
  }
  closeChartContextMenu()
}

const handleKeyDown = (event) => {
  if (event.key === 'Escape') {
    if (drawingMode.value) {
      drawingMode.value = null
      drawingStart.value = null
      tempDrawing.value = null
    }
    closeContextMenu()
    closeChartContextMenu()
  }
}

const handleChartClick = (event, tabId) => {
  if (!drawingMode.value) return

  const tab = tabs.value.find(t => t.id === tabId)
  if (!tab || !tab.chart || !tab.candlestickSeries) return

  const rect = chartRefs.value[tabId].getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  const time = tab.chart.timeScale().coordinateToTime(x)
  const price = tab.candlestickSeries.coordinateToPrice(y)

  if (!time || !price) return

  // Text drawing (single click)
  if (drawingMode.value === 'text' && tempDrawing.value) {
    const newDrawing = {
      id: Date.now().toString(),
      type: 'text',
      p1: { time, price },
      text: tempDrawing.value.text,
      color: tempDrawing.value.color,
      strokeWidth: 2,
      fontSize: 14
    }
    if (!tab.drawings) tab.drawings = []
    tab.drawings.push(newDrawing)
    drawingMode.value = null
    drawingStart.value = null
    tempDrawing.value = null
    saveUserTabs()
    updateDrawingCoordinates(tabId)
    broadcastSharedPatch(tabId, { drawings: tab.drawings })
    return
  }

  // Triangle drawing – collect three points
  if (drawingMode.value === 'triangle') {
    if (!drawingStart.value) {
      drawingStart.value = { time, price }
      tempDrawing.value = { type: 'triangle', points: [{ time, price }], color: selectedColor.value }
    } else if (tempDrawing.value.points.length === 1) {
      tempDrawing.value.points.push({ time, price })
    } else if (tempDrawing.value.points.length === 2) {
      // third point, finalize
      const points = [...tempDrawing.value.points, { time, price }]
      const newDrawing = { id: Date.now().toString(), type: 'triangle', points, color: selectedColor.value, strokeWidth: 2 }
      if (!tab.drawings) tab.drawings = []
      tab.drawings.push(newDrawing)
      // drawingMode.value = null // Keep tool selected
      drawingStart.value = null
      tempDrawing.value = null
      saveUserTabs()
      updateDrawingCoordinates(tabId)
      broadcastSharedPatch(tabId, { drawings: tab.drawings })
    }
    return
  }

  // Polygon drawing – collect points until double click (handled in mousemove/doubleclick)
  if (drawingMode.value === 'polygon') {
    if (!drawingStart.value) {
      drawingStart.value = { time, price }
      tempDrawing.value = { type: 'polygon', points: [{ time, price }], color: selectedColor.value }
    } else {
      tempDrawing.value.points.push({ time, price })
    }
    return
  }

  // Freehand drawing – collect continuous points while mouse is down
  if (drawingMode.value === 'freehand') {
    if (!drawingStart.value) {
      drawingStart.value = { time, price }
      tempDrawing.value = { type: 'freehand', points: [{ time, price }], color: selectedColor.value }
    } else {
      tempDrawing.value.points.push({ time, price })
    }
    return
  }

  // Default two‑point shapes (line, square, circle, arrow, hline, vline)
  if (!drawingStart.value) {
    drawingStart.value = { time, price }
    tempDrawing.value = {
      type: drawingMode.value,
      p1: { time, price },
      p2: { time, price },
      color: selectedColor.value
    }
  } else {
    const newDrawing = {
      id: Date.now().toString(),
      type: drawingMode.value,
      p1: drawingStart.value,
      p2: { time, price },
      color: selectedColor.value,
      strokeWidth: 2,
      fontSize: 14
    }
    if (!tab.drawings) tab.drawings = []
    tab.drawings.push(newDrawing)
    
    // Reset state but keep drawing mode
    // drawingMode.value = null // Keep tool selected
    drawingStart.value = null
    tempDrawing.value = null
    
    saveUserTabs()
    updateDrawingCoordinates(tabId)
    broadcastSharedPatch(tabId, { drawings: tab.drawings })
  }
}

const handleChartMouseMove = (event, tabId) => {
  if (!drawingMode.value || !drawingStart.value) return

  const tab = tabs.value.find(t => t.id === tabId)
  if (!tab || !tab.chart || !tab.candlestickSeries) return

  const rect = chartRefs.value[tabId].getBoundingClientRect()
  const x = event.clientX - rect.left
  const y = event.clientY - rect.top

  const time = tab.chart.timeScale().coordinateToTime(x)
  const price = tab.candlestickSeries.coordinateToPrice(y)

  if (time && price) {
    // For polygon and freehand, continuously add points
    if (drawingMode.value === 'polygon' || drawingMode.value === 'freehand') {
      if (tempDrawing.value) {
        // Only add if the mouse has moved significantly to avoid too many points
        const lastPoint = tempDrawing.value.points[tempDrawing.value.points.length - 1]
        if (!lastPoint || Math.abs(lastPoint.time - time) > 0.0001 || Math.abs(lastPoint.price - price) > 0.0001) {
          tempDrawing.value.points.push({ time, price })
        }
      }
    } else if (drawingMode.value === 'triangle') {
      // For triangle, update the last point if it's the 2nd or 3rd point being drawn
      if (tempDrawing.value && tempDrawing.value.points.length >= 1) {
        tempDrawing.value.points[tempDrawing.value.points.length - 1] = { time, price }
      }
    } else {
      // For two-point shapes, update the second point
      tempDrawing.value = {
        type: drawingMode.value,
        p1: drawingStart.value,
        p2: { time, price },
        color: selectedColor.value
      }
    }
    // Force update of temp drawing
    updateDrawingCoordinates(tabId) 
  }
}

const updateDrawingCoordinates = (tabId) => {
  const tab = tabs.value.find(t => t.id === tabId)
  if (!tab || !tab.chart || !tab.candlestickSeries) return

  const drawings = []
  
  // Process saved drawings
  if (tab.drawings) {
    tab.drawings.forEach(d => {
      if (d.points && d.points.length > 0) {
        const screenPoints = d.points.map(p => {
          const x = tab.chart.timeScale().timeToCoordinate(p.time)
          const y = tab.candlestickSeries.priceToCoordinate(p.price)
          return { x, y }
        }).filter(pt => pt.x !== null && pt.y !== null)
        if (screenPoints.length > 0) {
          const selected = selectedDrawing.value.tabId === tabId && selectedDrawing.value.drawingId === d.id
          drawings.push({
            id: d.id,
            type: d.type,
            points: screenPoints,
            color: d.color || '#2196F3',
            strokeWidth: d.strokeWidth ?? 2,
            selected
          })
        }
      } else {
        const x1 = tab.chart.timeScale().timeToCoordinate(d.p1.time)
        const y1 = tab.candlestickSeries.priceToCoordinate(d.p1.price)
        let x2 = null, y2 = null
        if (d.p2) {
          x2 = tab.chart.timeScale().timeToCoordinate(d.p2.time)
          y2 = tab.candlestickSeries.priceToCoordinate(d.p2.price)
        }
        if (x1 !== null && y1 !== null) {
          const selected = selectedDrawing.value.tabId === tabId && selectedDrawing.value.drawingId === d.id
          drawings.push({
            id: d.id,
            type: d.type,
            x1, y1, x2, y2,
            color: d.color || '#2196F3',
            text: d.text,
            strokeWidth: d.strokeWidth ?? 2,
            fontSize: d.fontSize ?? 14,
            selected
          })
        }
      }
    })
  }

  // Process temp drawing
  if (tempDrawing.value) {
    const d = tempDrawing.value
    // For polygon / freehand / triangle we have an array of points
    if (d.points && d.points.length > 0) {
      const screenPoints = d.points.map(p => {
        const x = tab.chart.timeScale().timeToCoordinate(p.time)
        const y = tab.candlestickSeries.priceToCoordinate(p.price)
        return { x, y }
      }).filter(pt => pt.x !== null && pt.y !== null)
      if (screenPoints.length > 0) {
        drawings.push({
          id: 'temp',
          type: d.type,
          points: screenPoints,
          color: d.color || '#2196F3',
          isTemp: true
        })
      }
    } else {
      const x1 = tab.chart.timeScale().timeToCoordinate(d.p1.time)
      const y1 = tab.candlestickSeries.priceToCoordinate(d.p1.price)
      let x2 = null, y2 = null
      if (d.p2) {
        x2 = tab.chart.timeScale().timeToCoordinate(d.p2.time)
        y2 = tab.candlestickSeries.priceToCoordinate(d.p2.price)
      }
      if (x1 !== null && y1 !== null) {
        drawings.push({
          id: 'temp',
          type: d.type,
          x1, y1, x2, y2,
          color: d.color || '#2196F3',
          text: d.text,
          isTemp: true
        })
      }
    }
  }

  renderedDrawings.value = {
    ...renderedDrawings.value,
    [tabId]: drawings
  }
}

const handleDragStart = (event, tab, index) => {
  if (editingTab.value && editingTab.value.id === tab.id) {
    event.preventDefault()
    return
  }
  draggedTabId.value = tab.id
  draggedTabIndex.value = index
  event.dataTransfer.effectAllowed = 'move'
  event.dataTransfer.setData('text/plain', tab.id.toString())
  // Add a slight delay to allow drag image to be set
  setTimeout(() => {
    if (event.target) {
      event.target.style.opacity = '0.5'
    }
  }, 0)
}

const handleDragEnd = (event) => {
  if (event.target) {
    event.target.style.opacity = ''
  }
  draggedTabId.value = null
  draggedTabIndex.value = null
  dragOverIndex.value = null
}

const handleDragOver = (event, index) => {
  if (draggedTabId.value === null) return
  dragOverIndex.value = index
  event.dataTransfer.dropEffect = 'move'
}

const handleDragLeave = (event, index) => {
  // Only clear drag over if we're actually leaving the element (not entering a child)
  const rect = event.currentTarget.getBoundingClientRect()
  const x = event.clientX
  const y = event.clientY
  
  if (x < rect.left || x > rect.right || y < rect.top || y > rect.bottom) {
    dragOverIndex.value = null
  }
}

const handleDrop = (event, dropIndex) => {
  event.preventDefault()
  
  if (draggedTabId.value === null || draggedTabIndex.value === null) {
    return
  }
  
  const dragIndex = draggedTabIndex.value
  
  if (dragIndex === dropIndex) {
    dragOverIndex.value = null
    return
  }
  
  // Reorder tabs
  const tabToMove = tabs.value[dragIndex]
  tabs.value.splice(dragIndex, 1)
  tabs.value.splice(dropIndex, 0, tabToMove)
  
  // Save new order
  saveUserTabs()
  
  // Reset drag state
  draggedTabId.value = null
  draggedTabIndex.value = null
  dragOverIndex.value = null
}

const handleEarningsTickerSelect = (symbol) => {
  // Switch to Stocks tab and select the ticker
  const stocksTab = tabs.value.find(t => t.type === 'stocks')
  if (stocksTab) {
    activeTab.value = stocksTab.id
    nextTick(() => {
      selectTicker(stocksTab.id, symbol)
    })
  }
}

const handleViewBot = (bot) => {
  console.log('View bot:', bot)
  // TODO: Implement bot details view
  alert(`Viewing details for ${bot.name}`)
}

const handleCompete = (bot) => {
  console.log('Compete with bot:', bot)
  // TODO: Implement competition feature
  alert(`Starting competition with ${bot.name}`)
}



const handleCreateBot = () => {
  // Bot creation is now handled in BotList component
  console.log('Create bot event received')
}

const handleLoginSuccess = (userData) => {
  showLoginModal.value = false
  // Auth is already handled in LoginModal
}

const handleRegisterSuccess = (userData) => {
  showRegisterModal.value = false
  // Auth is already handled in RegisterModal
}

const handleLogout = async () => {
  await authStore.logout()
  // Redirect to home
  window.location.href = '/'
}

const handleViewProfile = () => {
  showProfileModal.value = true
}

const handleProfileSaved = () => {
  // Profile was updated, refresh user data
  if (authStore) {
    authStore.fetchUser()
  }
}

const setTimeframe = async (tabId, tf) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab) {
    tab.timeframe = tf
    if (tab.selectedTicker) {
      // Update quote with new timeframe to recalculate change/change%
      try {
        const response = await api.getQuote(tab.selectedTicker, tf)
        const quote = response.data
        if (tab.chartInfo) {
          tab.chartInfo.change = quote.change
          tab.chartInfo.changePercent = quote.changePercent
        }
      } catch (error) {
        console.error('Failed to update quote:', error)
      }
      await loadChart(tabId)
    }
    broadcastSharedPatch(tabId, { timeframe: tab.timeframe })
  }
}

const updateTabConfig = (tabId, config) => {
  const tab = tabs.value.find(t => t.id === tabId)
  if (tab) {
    tab.chatConfig = { ...tab.chatConfig, ...config }
    saveUserTabs()
  }
}

const setChartType = (tabId, type) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab) {
    tab.chartType = type
    if (tab.selectedTicker) {
      loadChart(tabId)
    }
    broadcastSharedPatch(tabId, { chartType: tab.chartType })
  }
}

const toggleIndicator = (tabId, indicator) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab) {
    if (!tab.indicators) {
      tab.indicators = {
        rsi: false,
        ma13: false,
        ma50: false,
        ma200: false,
        ma800: false,
        bullRun: false
      }
    }
    tab.indicators[indicator] = !tab.indicators[indicator]
    // Save settings for this ticker
    if (tab.selectedTicker) {
      saveIndicatorSettings(tab.selectedTicker, tab.indicators)
      loadChart(tabId)
    }
    broadcastSharedPatch(tabId, { indicators: tab.indicators })
  }
}

const handleAIAnalysis = async (tabId) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab || !tab.selectedTicker || !tab.aiQuery.trim()) return

  tab.aiLoading = true
  try {
    const response = await api.analyzeChart({
      ticker: tab.selectedTicker,
      timeframe: tab.timeframe,
      query: tab.aiQuery
    })
    
    const result = response.data
    // Backend now returns { data: [indicator1, indicator2, ...] }
    const indicators = result.data || []
    let shouldReload = false
    
    // Initialize indicators if missing
    if (!tab.indicators) {
      tab.indicators = {
        rsi: false,
        ma13: false,
        ma50: false,
        ma200: false,
        ma800: false,
        bullRun: false
      }
    }
    
    if (indicators.length > 0) {
      for (const indicatorResult of indicators) {
        // Add indicator to chart
        const indicatorType = indicatorResult.indicator
        const data = indicatorResult.data
        const config = indicatorResult.config
        const params = config.params || {}
        const color = config.color || '#2196F3'
        
        // Check if this matches a standard indicator button
        let isStandard = false
        
        if (indicatorType === 'RSI' && (params.period == 14 || !params.period)) {
          tab.indicators.rsi = !tab.indicators.rsi // Toggle or just enable? User said "light up and turn off", implying toggle or sync. Let's enable if asking to add.
          // Actually, if the user says "add RSI", they expect it to appear. If it's already there, maybe they want to remove it?
          // But the AI parser usually just says "RSI". 
          // Let's assume "ensure it is on".
          tab.indicators.rsi = true
          isStandard = true
        } else if ((indicatorType === 'SMA' || indicatorType === 'MA')) {
          if (params.period == 13) { tab.indicators.ma13 = true; isStandard = true; }
          else if (params.period == 50) { tab.indicators.ma50 = true; isStandard = true; }
          else if (params.period == 200) { tab.indicators.ma200 = true; isStandard = true; }
          else if (params.period == 800) { tab.indicators.ma800 = true; isStandard = true; }
        }
        
        if (isStandard) {
          shouldReload = true
          continue // Skip adding as custom series
        }
        
        if (indicatorType === 'BB') {
          // Bollinger Bands (Area/Lines)
          const upperSeries = tab.chart.addLineSeries({
            color: color,
            lineWidth: 1,
            title: 'BB Upper'
          })
          const lowerSeries = tab.chart.addLineSeries({
            color: color,
            lineWidth: 1,
            title: 'BB Lower'
          })
          const basisSeries = tab.chart.addLineSeries({
            color: color,
            lineWidth: 1,
            lineStyle: 2, // Dashed
            title: 'BB Basis'
          })
          
          upperSeries.setData(data.map(d => ({ time: d.time / 1000, value: d.upper })))
          lowerSeries.setData(data.map(d => ({ time: d.time / 1000, value: d.lower })))
          basisSeries.setData(data.map(d => ({ time: d.time / 1000, value: d.basis })))
          
          if (!tab.aiIndicators) tab.aiIndicators = []
          tab.aiIndicators.push({ type: 'BB', series: [upperSeries, lowerSeries, basisSeries] })
          
        } else if (['SMA', 'EMA'].includes(indicatorType)) {
          // Moving Averages
          const series = tab.chart.addLineSeries({
            color: color,
            lineWidth: 2,
            title: `${indicatorType} ${config.params.period}`
          })
          
          series.setData(data.map(d => ({ time: d.time / 1000, value: d.value })))
          
          if (!tab.aiIndicators) tab.aiIndicators = []
          tab.aiIndicators.push({ type: indicatorType, series: [series] })
          
        } else if (indicatorType === 'RSI') {
          // RSI (Separate Pane)
          const series = tab.chart.addLineSeries({
            color: color,
            lineWidth: 2,
            priceScaleId: 'ai_rsi',
            title: `RSI ${config.params.period}`
          })
          
          tab.chart.priceScale('ai_rsi').applyOptions({
            scaleMargins: {
              top: 0.1,
              bottom: 0.1,
            },
          })
          
          series.setData(data.map(d => ({ time: d.time / 1000, value: d.value })))
          
          if (!tab.aiIndicators) tab.aiIndicators = []
          tab.aiIndicators.push({ type: 'RSI', series: [series] })
          
        } else if (indicatorType === 'MACD') {
          // MACD (Separate Pane)
          const histogramSeries = tab.chart.addHistogramSeries({
            color: '#26a69a',
            priceScaleId: 'ai_macd',
            title: 'MACD Histogram'
          })
          const macdSeries = tab.chart.addLineSeries({
            color: '#2962FF',
            lineWidth: 2,
            priceScaleId: 'ai_macd',
            title: 'MACD'
          })
          const signalSeries = tab.chart.addLineSeries({
            color: '#FF6D00',
            lineWidth: 2,
            priceScaleId: 'ai_macd',
            title: 'Signal'
          })
          
          tab.chart.priceScale('ai_macd').applyOptions({
            scaleMargins: {
              top: 0.1,
              bottom: 0.1,
            },
          })
          
          histogramSeries.setData(data.map(d => ({ 
            time: d.time / 1000, 
            value: d.histogram,
            color: d.histogram >= 0 ? '#26a69a' : '#ef5350'
          })))
          macdSeries.setData(data.map(d => ({ time: d.time / 1000, value: d.macd })))
          signalSeries.setData(data.map(d => ({ time: d.time / 1000, value: d.signal })))
          
          if (!tab.aiIndicators) tab.aiIndicators = []
          tab.aiIndicators.push({ type: 'MACD', series: [histogramSeries, macdSeries, signalSeries] })
  
        } else if (indicatorType === 'VOL') {
          // Volume (Separate Pane)
          const volumeSeries = tab.chart.addHistogramSeries({
            color: '#26a69a',
            priceScaleId: 'ai_vol',
            title: 'Volume'
          })
          
          tab.chart.priceScale('ai_vol').applyOptions({
            scaleMargins: {
              top: 0.1,
              bottom: 0.1,
            },
          })
          
          volumeSeries.setData(data.map(d => ({ 
            time: d.time / 1000, 
            value: d.value,
            color: d.color
          })))
          
          if (!tab.aiIndicators) tab.aiIndicators = []
          tab.aiIndicators.push({ type: 'VOL', series: [volumeSeries] })
  
        } else if (indicatorType === 'STOCH') {
          // Stochastic (Separate Pane)
          const kSeries = tab.chart.addLineSeries({
            color: '#2962FF',
            lineWidth: 2,
            priceScaleId: 'ai_stoch',
            title: '%K'
          })
          const dSeries = tab.chart.addLineSeries({
            color: '#FF6D00',
            lineWidth: 2,
            priceScaleId: 'ai_stoch',
            title: '%D'
          })
          
          tab.chart.priceScale('ai_stoch').applyOptions({
            scaleMargins: {
              top: 0.1,
              bottom: 0.1,
            },
          })
          
          kSeries.setData(data.map(d => ({ time: d.time / 1000, value: d.k })))
          dSeries.setData(data.map(d => ({ time: d.time / 1000, value: d.d })))
          
          if (!tab.aiIndicators) tab.aiIndicators = []
          tab.aiIndicators.push({ type: 'STOCH', series: [kSeries, dSeries] })
        }
      }
      
      tab.aiQuery = '' // Clear input on success
      
      if (shouldReload) {
        saveIndicatorSettings(tab.selectedTicker, tab.indicators)
        loadChart(tabId)
      }
    }
  } catch (error) {
    console.error('AI Analysis failed:', error)
    alert('Failed to analyze chart: ' + (error.response?.data?.detail || error.message))
  } finally {
    tab.aiLoading = false
  }
}


const updateChartInfo = async (tabId) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab || !tab.chartInfo || !tab.chartInfo.symbol) return

  try {
    const response = await api.getQuote(tab.chartInfo.symbol)
    const quote = response.data
    tab.chartInfo.name = quote.name || tab.chartInfo.name
    tab.chartInfo.price = quote.price
    tab.chartInfo.change = quote.change
    tab.chartInfo.changePercent = quote.changePercent
    tab.chartInfo.volume = quote.volume
    tab.chartInfo.open = quote.open
    tab.chartInfo.high = quote.high
    tab.chartInfo.low = quote.low
    tab.chartInfo.previousClose = quote.previousClose
    // Extended hours data
    tab.chartInfo.postMarketPrice = quote.postMarketPrice
    tab.chartInfo.postMarketChange = quote.postMarketChange
    tab.chartInfo.postMarketChangePercent = quote.postMarketChangePercent
    tab.chartInfo.preMarketPrice = quote.preMarketPrice
    tab.chartInfo.preMarketChange = quote.preMarketChange
    tab.chartInfo.preMarketChangePercent = quote.preMarketChangePercent
    tab.chartInfo.marketState = quote.marketState
  } catch (error) {
    console.error('Failed to update chart info:', error)
  }
}

const handleSearch = async () => {
  // Clear previous timeout
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
    searchTimeout.value = null
  }
  
  // Clear results if query is empty
  if (searchQuery.value.length === 0) {
    searchResults.value = []
    searchLoading.value = false
    return
  }
  
  // For very short queries (1 char), don't search yet
  if (searchQuery.value.length === 1) {
    searchLoading.value = false
    searchResults.value = []
    return
  }
  
  // Debounce search - wait 400ms after user stops typing
  searchTimeout.value = setTimeout(async () => {
    // Capture current query at the start
    const currentQuery = searchQuery.value
    
    if (currentQuery.length < 2) {
      searchLoading.value = false
      searchResults.value = []
      return
    }
    
    // Show loading only if query hasn't changed
    if (currentQuery === searchQuery.value) {
      searchLoading.value = true
    }
    
    try {
      // Add timeout to prevent hanging (3 seconds - fast feedback)
      const timeoutPromise = new Promise((_, reject) => {
        setTimeout(() => reject(new Error('Search timeout')), 3000)
      })
      
      const searchPromise = api.search(currentQuery)
      const response = await Promise.race([searchPromise, timeoutPromise])
      
      // Check if query changed while waiting - if so, ignore results
      if (currentQuery !== searchQuery.value) {
        console.log('Query changed during search, ignoring results')
        return
      }
      
      if (response.data && response.data.results) {
        searchResults.value = response.data.results
        selectedResultIndex.value = null // Reset selection on new results
      } else {
        searchResults.value = []
      }
    } catch (error) {
      // Check if query changed during error
      if (currentQuery !== searchQuery.value) {
        return
      }
      
      // Handle timeout or errors - try to use query as direct ticker if it looks like one
      const queryUpper = currentQuery.trim().toUpperCase()
      if (queryUpper.length >= 1 && queryUpper.length <= 10) {
        // Detect asset type based on symbol pattern
        let assetType = 'EQUITY'
        if (queryUpper.endsWith('-USD') || queryUpper.endsWith('-EUR') || queryUpper.endsWith('-GBP')) {
          assetType = 'CRYPTOCURRENCY'
        } else if (queryUpper.endsWith('=F')) {
          assetType = 'FUTURE'
        } else if (queryUpper.startsWith('^')) {
          assetType = 'INDEX'
        }
        
        // Check if it looks like a valid ticker (alphanumeric with allowed separators)
        const cleaned = queryUpper.replace(/[-=^.]/g, '')
        if (cleaned.match(/^[A-Z0-9]+$/)) {
          searchResults.value = [{
            symbol: queryUpper,
            name: queryUpper,
            type: assetType,
            exchange: 'N/A'
          }]
          selectedResultIndex.value = null // Reset selection
        } else {
          searchResults.value = []
        }
      } else {
        searchResults.value = []
      }
    } finally {
      // Only update loading state if query hasn't changed
      if (currentQuery === searchQuery.value) {
        searchLoading.value = false
      }
    }
  }, 400) // 400ms debounce - good balance between responsiveness and performance
}

const getAssetTypeLabel = (type) => {
  const typeMap = {
    'EQUITY': 'Stock',
    'ETF': 'ETF',
    'CRYPTOCURRENCY': 'Crypto',
    'FUTURE': 'Future',
    'INDEX': 'Index',
    'OPTION': 'Option',
    'CURRENCY': 'Currency'
  }
  return typeMap[type] || type || 'Asset'
}

const getAssetTypeIcon = (type) => {
  const iconMap = {
    'EQUITY': '📈',
    'ETF': '📊',
    'CRYPTOCURRENCY': '₿',
    'FUTURE': '📉',
    'INDEX': '📋',
    'OPTION': '⚡',
    'CURRENCY': '💱'
  }
  return iconMap[type] || '📌'
}

const getAssetTypeClass = (type) => {
  const classMap = {
    'EQUITY': 'type-equity',
    'ETF': 'type-etf',
    'CRYPTOCURRENCY': 'type-crypto',
    'FUTURE': 'type-future',
    'INDEX': 'type-index',
    'OPTION': 'type-option',
    'CURRENCY': 'type-currency'
  }
  return classMap[type] || 'type-default'
}

const navigateResults = (direction) => {
  if (searchResults.value.length === 0) return
  
  if (selectedResultIndex.value === null) {
    selectedResultIndex.value = direction > 0 ? 0 : searchResults.value.length - 1
  } else {
    selectedResultIndex.value += direction
    if (selectedResultIndex.value < 0) {
      selectedResultIndex.value = searchResults.value.length - 1
    } else if (selectedResultIndex.value >= searchResults.value.length) {
      selectedResultIndex.value = 0
    }
  }
}

const addTopResult = () => {
  if (searchResults.value.length > 0) {
    const currentTab = tabs.value.find(t => t.id === activeTab.value)
    const indexToAdd = selectedResultIndex.value !== null ? selectedResultIndex.value : 0
    addToWatchlist(searchResults.value[indexToAdd], currentTab.id)
    selectedResultIndex.value = null
  }
}

const focusSearchInput = () => {
  nextTick(() => {
    searchInputRef.value?.focus()
  })
}

const handleResultClick = async (item, tabId) => {
  if (isAddingToWatchlist.value) {
    console.log('Already adding to watchlist, ignoring click')
    return
  }
  console.log('Result clicked:', item, 'tabId:', tabId)
  await addToWatchlist(item, tabId)
}

const addToWatchlist = async (item, tabId) => {
  if (!item || !item.symbol) {
    console.error('Invalid item:', item)
    return
  }
  
  if (isAddingToWatchlist.value) {
    console.log('Already adding to watchlist')
    return
  }
  
  isAddingToWatchlist.value = true
  
  try {
    console.log('Adding to watchlist:', item.symbol, item.name, 'tabId:', tabId)
    
    // Find the current active tab - use the Stocks tab (type === 'stocks')
    let targetTabId = tabId
    if (!targetTabId) {
      // Find the first Stocks tab
      const stocksTab = tabs.value.find(t => t && t.type === 'stocks')
      targetTabId = stocksTab ? stocksTab.id : activeTab.value
    }
    
    // Verify the tab exists and is a stocks tab
    const targetTab = tabs.value.find(t => t && t.id === targetTabId)
    if (!targetTab || targetTab.type !== 'stocks') {
      // Find or create a stocks tab
      const stocksTab = tabs.value.find(t => t && t.type === 'stocks')
      if (stocksTab) {
        targetTabId = stocksTab.id
      } else {
        console.error('No stocks tab found')
        return
      }
    }
    
    console.log('Using tabId:', targetTabId)
    console.log('Current activeTab before activation:', activeTab.value)
    
    // Activate the tab if it's not already active
    if (activeTab.value !== targetTabId) {
      console.log('Activating tab:', targetTabId)
      try {
        setActiveTab(targetTabId)
        await nextTick()
        await new Promise(resolve => setTimeout(resolve, 200))
        console.log('Tab activated, new activeTab:', activeTab.value)
      } catch (error) {
        console.error('Error activating tab:', error)
        throw error
      }
    } else {
      console.log('Tab already active')
    }
    
    console.log('Adding item to watchlist store...')
    try {
      await watchlistStore.addItem(item.symbol, item.name || item.symbol)
      console.log('WatchlistStore.addItem completed successfully')
      console.log('Current watchlist after add:', watchlist.value)
    } catch (error) {
      console.error('Error in watchlistStore.addItem:', error)
      console.error('Error details:', error.response?.data || error.message)
      alert(`Failed to add ${item.symbol} to watchlist: ${error.response?.data?.detail || error.message || 'Unknown error'}`)
      return // Stop here if there's an error
    }
    console.log('Item added to watchlist, clearing search...')
    searchQuery.value = ''
    searchResults.value = []
    
    // Force a reactive update
    await nextTick()
    console.log('Watchlist after nextTick:', watchlist.value)
    
    // Wait a bit for the watchlist to update and DOM to be ready
    console.log('Waiting for DOM to be ready...')
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 300))
    
    // Verify tab is still active and visible
    const currentActiveTab = activeTab.value
    console.log('Current activeTab:', currentActiveTab, 'Target tab:', targetTabId)
    if (currentActiveTab !== targetTabId) {
      console.log('Tab changed, activating target tab again')
      setActiveTab(targetTabId)
      await nextTick()
      await new Promise(resolve => setTimeout(resolve, 200))
    }
    
    console.log('Selecting ticker:', item.symbol, 'on tab:', targetTabId)
    await selectTicker(targetTabId, item.symbol)
    console.log('selectTicker completed')
  } catch (error) {
    console.error('Error adding to watchlist:', error)
    console.error('Error response:', error.response)
    console.error('Error stack:', error.stack)
    alert(`Failed to add ${item.symbol} to watchlist: ${error.response?.data?.detail || error.message || 'Unknown error'}`)
  } finally {
    isAddingToWatchlist.value = false
  }
}

const removeSelected = async (tabId) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (tab && tab.selectedTicker) {
    await watchlistStore.removeItem(tab.selectedTicker)
    tab.selectedTicker = null
    tab.chartInfo = {
      symbol: '',
      name: '',
      price: null,
      change: null,
      changePercent: null,
      volume: null
    }
    if (tab.chart) {
      tab.chart.remove()
      tab.chart = null
    }
    
    if (watchlist.value.length > 0) {
      selectTicker(tabId, watchlist.value[0].symbol)
    }
  }
}

const selectTicker = async (tabId, symbol) => {
  console.log('selectTicker called:', { tabId, symbol })
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab) {
    console.error('Tab not found:', tabId, 'Available tabs:', tabs.value.map(t => t?.id))
    return
  }
  
  tab.selectedTicker = symbol
  tab.chartInfo.symbol = symbol
  
  // Ensure DOM is ready for the chart container
  await nextTick()
  
  // Fire quote and chart loading in PARALLEL (biggest speed win)
  const quotePromise = api.getQuote(symbol, tab.timeframe || '1d')
    .then(response => {
      const quote = response.data
      tab.chartInfo.name = quote.name
      tab.chartInfo.price = quote.price
      tab.chartInfo.change = quote.change
      tab.chartInfo.changePercent = quote.changePercent
      tab.chartInfo.volume = quote.volume
      // Copy extended hours & OHLC data
      if (quote.open != null) tab.chartInfo.open = quote.open
      if (quote.high != null) tab.chartInfo.high = quote.high
      if (quote.low != null) tab.chartInfo.low = quote.low
      if (quote.postMarketPrice != null) tab.chartInfo.postMarketPrice = quote.postMarketPrice
      if (quote.postMarketChange != null) tab.chartInfo.postMarketChange = quote.postMarketChange
      if (quote.postMarketChangePercent != null) tab.chartInfo.postMarketChangePercent = quote.postMarketChangePercent
      if (quote.preMarketPrice != null) tab.chartInfo.preMarketPrice = quote.preMarketPrice
      if (quote.preMarketChange != null) tab.chartInfo.preMarketChange = quote.preMarketChange
      if (quote.preMarketChangePercent != null) tab.chartInfo.preMarketChangePercent = quote.preMarketChangePercent
      if (quote.marketState) tab.chartInfo.marketState = quote.marketState
      console.log('Quote loaded:', quote)
    })
    .catch(error => {
      console.error('Failed to get quote:', error)
    })

  const chartPromise = loadChart(tabId)

  // Wait for both to complete
  await Promise.allSettled([quotePromise, chartPromise])
  
  if (activeTab.value === tabId) startChartRefresh(tabId)
  broadcastSharedPatch(tabId, {
    selectedTicker: symbol,
    timeframe: tab.timeframe,
    chartType: tab.chartType,
    indicators: tab.indicators || null,
    drawings: tab.drawings || []
  })
}


const loadChart = async (tabId, forceRefresh = false) => {
  console.log('loadChart called:', tabId, forceRefresh ? '(refresh)' : '')
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab || !tab.selectedTicker) {
    console.error('Tab or ticker not found:', { tab: !!tab, ticker: tab?.selectedTicker })
    return
  }

  // Real-time refresh: update series data only (no chart teardown)
  if (forceRefresh && tab.chart && (tab.candlestickSeries || tab.lineSeries)) {
    try {
      const response = await api.getChart({
        ticker: tab.selectedTicker,
        timeframe: tab.timeframe,
        chart_type: tab.chartType.toLowerCase()
      })
      const chartData = response.data
      if (!chartData?.data?.length) return
      const cacheKey = `${tab.selectedTicker}_${tab.timeframe}_${tab.chartType}`
      setCached('chart', chartData, cacheKey)
      tab.chartData = chartData.data
      const data = chartData.data
      const earningsDates = chartData.earnings_dates || []
      if (tab.chartType === 'Candle' && tab.candlestickSeries) {
        tab.candlestickSeries.setData(data.map(d => ({
          time: d.time / 1000,
          open: d.open,
          high: d.high,
          low: d.low,
          close: d.close,
        })))
        if (earningsDates.length > 0) {
          const markers = earningsDates.map(earning => {
            const earningsTime = earning.timestamp / 1000
            let closest = data[0]
            let minDiff = Math.abs(data[0].time / 1000 - earningsTime)
            for (const p of data) {
              const diff = Math.abs(p.time / 1000 - earningsTime)
              if (diff < minDiff) { minDiff = diff; closest = p }
            }
            return { time: closest.time / 1000, position: 'aboveBar', color: '#ff9800', shape: 'arrowDown', size: 3, text: 'E' }
          })
          tab.candlestickSeries.setMarkers(markers)
        }
      } else if (tab.lineSeries) {
        const lineData = data.map(d => ({ time: d.time / 1000, value: d.close })).filter(d => !isNaN(d.value))
        if (lineData.length > 0) tab.lineSeries.setData(lineData)
        if (earningsDates.length > 0 && lineData.length > 0) {
          const markers = earningsDates.map(earning => {
            const earningsTime = earning.timestamp / 1000
            let closest = lineData[0]
            let minDiff = Math.abs(lineData[0].time - earningsTime)
            for (const p of lineData) {
              const diff = Math.abs(p.time - earningsTime)
              if (diff < minDiff) { minDiff = diff; closest = p }
            }
            return { time: closest.time, position: 'aboveBar', color: '#ff9800', shape: 'arrowDown', size: 3, text: 'E' }
          })
          tab.lineSeries.setMarkers(markers)
        }
      }
      await updateChartInfo(tabId)
      return
    } catch (e) {
      console.error('Chart refresh error:', e)
    }
    return
  }

  let chartContainer = chartRefs.value[tabId]
  if (!chartContainer) {
    console.error('Chart container not found for tab:', tabId, 'Available refs:', Object.keys(chartRefs.value))
    // Try to wait a bit more for the DOM to be ready
    await nextTick()
    await new Promise(resolve => setTimeout(resolve, 50))
    chartContainer = chartRefs.value[tabId]
    if (!chartContainer) {
      console.error('Chart container still not found after retry')
      return
    }
  }

  // Ensure container has valid dimensions
  if (chartContainer.clientWidth === 0 || chartContainer.clientHeight === 0) {
    console.warn('Chart container has zero dimensions, waiting for layout...')
    await new Promise(resolve => setTimeout(resolve, 50))
    // Retry getting dimensions
    if (chartContainer.clientWidth === 0 || chartContainer.clientHeight === 0) {
      console.error('Chart container still has zero dimensions:', {
        width: chartContainer.clientWidth,
        height: chartContainer.clientHeight
      })
      // Use fallback dimensions
      chartContainer.style.width = '100%'
      chartContainer.style.height = '100%'
    }
  }


  try {
    // Check cache first (skip cache when force-refreshing)
    const cacheKey = `${tab.selectedTicker}_${tab.timeframe}_${tab.chartType}`
    let chartData = forceRefresh ? null : getCached('chart', cacheKey)
    
    if (!chartData || !chartData.data || chartData.data.length === 0) {
      console.log('Fetching chart data from API for', tab.selectedTicker)
      // Fetch from API
      const response = await api.getChart({
        ticker: tab.selectedTicker,
        timeframe: tab.timeframe,
        chart_type: tab.chartType.toLowerCase()
      })
      chartData = response.data
      console.log('Chart data received:', { 
        dataPoints: chartData.data?.length || 0,
        earningsDates: chartData.earnings_dates?.length || 0
      })
      // Cache the response
      // Cache the response
      setCached('chart', chartData, cacheKey)
    } else {
      console.log('Using cached chart data for', tab.selectedTicker, 'points:', chartData.data?.length || 0)
    }

    if (!chartData || !chartData.data || chartData.data.length === 0) {
      console.error('No chart data available')
      return
    }
    
    // Store chart data in tab for AI context
    tab.chartData = chartData.data

    await nextTick()

    const data = chartData.data
    const earningsDates = chartData.earnings_dates || []

    if (tab.chart) {
      // Remove earnings lines if they exist
      if (tab.earningsLines && tab.earningsLines.length > 0) {
        tab.earningsLines.forEach(line => {
          try {
            tab.chart.removeSeries(line)
          } catch (e) {
            // Series might already be removed
          }
        })
        tab.earningsLines = []
      }
      tab.chart.remove()
    }

    const containerWidth = chartContainer.clientWidth || 800
    const containerHeight = chartContainer.clientHeight || 600

    console.log('Creating chart with dimensions:', { width: containerWidth, height: containerHeight })

    tab.chart = createChart(chartContainer, {
      width: containerWidth,
      height: containerHeight,
      layout: {
        background: { type: 'solid', color: 'transparent' },
        textColor: '#94a3b8',
      },
      grid: {
        vertLines: { color: 'rgba(255, 255, 255, 0.05)' },
        horzLines: { color: 'rgba(255, 255, 255, 0.05)' },
      },
      timeScale: {
        timeVisible: true,
        secondsVisible: false,
      },
    })

    // Subscribe to visible time range changes to update drawings
    tab.chart.timeScale().subscribeVisibleTimeRangeChange(() => {
      updateDrawingCoordinates(tabId)
    })
    
    // Subscribe to visible logical range changes for dynamic data loading
    tab.chart.timeScale().subscribeVisibleLogicalRangeChange((logicalRange) => {
      if (logicalRange && logicalRange.from < 20) {
        // User is near the start of data, try to load more
        checkAndLoadMoreData(tabId)
      }
    })
    
    // Also update on resize
    if (!tab.resizeObserver) {
      tab.resizeObserver = new ResizeObserver(() => {
        updateDrawingCoordinates(tabId)
      })
      tab.resizeObserver.observe(chartContainer)
    }

    // Initialize indicators state if not exists, load from cache if available
    if (!tab.indicators) {
      const savedSettings = loadIndicatorSettings(tab.selectedTicker)
      tab.indicators = savedSettings || {
        rsi: true,
        ma13: false,
        ma50: false,
        ma200: false,
        ma800: false,
        bullRun: true
      }
    }
    
    // Debug: log earnings dates
    if (earningsDates.length > 0) {
      console.log(`Found ${earningsDates.length} earnings dates for ${tab.selectedTicker}:`, earningsDates)
    } else {
      console.log(`No earnings dates found for ${tab.selectedTicker}`)
    }

    if (tab.chartType === 'Candle') {
      tab.candlestickSeries = tab.chart.addCandlestickSeries({
        upColor: '#26a69a',
        downColor: '#ef5350',
        borderVisible: false,
        wickUpColor: '#26a69a',
        wickDownColor: '#ef5350',
      })
      tab.candlestickSeries.setData(data.map(d => ({
        time: d.time / 1000,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      })))
      
      // Add earnings markers
      if (earningsDates.length > 0) {
        const markers = earningsDates.map(earning => {
          // Find the closest data point to the earnings date
          const earningsTime = earning.timestamp / 1000
          let closestDataPoint = data[0]
          let minDiff = Math.abs(data[0].time / 1000 - earningsTime)
          
          for (const point of data) {
            const diff = Math.abs(point.time / 1000 - earningsTime)
            if (diff < minDiff) {
              minDiff = diff
              closestDataPoint = point
            }
          }
          
          return {
            time: closestDataPoint.time / 1000,
            position: 'aboveBar',
            color: '#ff9800',
            shape: 'arrowDown',
            size: 3,
            text: 'E',
          }
        })
        
        tab.candlestickSeries.setMarkers(markers)
      }
    } else {
      tab.lineSeries = tab.chart.addLineSeries({
        color: '#2196F3',
        lineWidth: 2,
      })
      
      const lineData = data.map(d => ({
        time: d.time / 1000,
        value: d.close,
      })).filter(d => !isNaN(d.value))
      
      if (lineData.length > 0) {
        tab.lineSeries.setData(lineData)
      }
      
      // Add earnings markers
      if (earningsDates.length > 0 && lineData.length > 0) {
        const markers = earningsDates.map(earning => {
          // Find the closest data point to the earnings date
          const earningsTime = earning.timestamp / 1000
          let closestDataPoint = lineData[0]
          let minDiff = Math.abs(lineData[0].time - earningsTime)
          
          for (const point of lineData) {
            const diff = Math.abs(point.time - earningsTime)
            if (diff < minDiff) {
              minDiff = diff
              closestDataPoint = point
            }
          }
          
          return {
            time: closestDataPoint.time,
            position: 'aboveBar',
            color: '#ff9800',
            shape: 'arrowDown',
            size: 3,
            text: 'E',
          }
        })
        
        tab.lineSeries.setMarkers(markers)
      }
    }

    // Add vertical lines for earnings using a separate series
    if (earningsDates.length > 0 && data.length > 0) {
      // Find min and max prices in the dataset
      const allPrices = data.flatMap(d => [d.high, d.low, d.close, d.open].filter(p => p != null))
      const minPrice = Math.min(...allPrices)
      const maxPrice = Math.max(...allPrices)
      const pricePadding = (maxPrice - minPrice) * 0.02 // 2% padding
      
      // Create vertical lines using a line series
      earningsDates.forEach(earning => {
        const earningsTime = earning.timestamp / 1000
        
        // Find the closest data point to the earnings date
        let closestDataPoint = data[0]
        let minDiff = Math.abs(data[0].time / 1000 - earningsTime)
        
        for (const point of data) {
          const diff = Math.abs(point.time / 1000 - earningsTime)
          if (diff < minDiff) {
            minDiff = diff
            closestDataPoint = point
          }
        }
        
        const earningsTimestamp = closestDataPoint.time / 1000
        
        // Create a vertical line using a line series
        // We use many points with very small time increments to create a vertical line
        const verticalLineSeries = tab.chart.addLineSeries({
          color: '#ff9800',
          lineWidth: 3,
          lineStyle: 0, // Solid
          priceLineVisible: false,
          lastValueVisible: false,
          crosshairMarkerVisible: false,
          pointMarkersVisible: false,
        })
        
        // Create points for vertical line: from min to max price with same timestamp
        // We use a small time increment to ensure points are ordered correctly
        const verticalPoints = []
        const numPoints = 200 // More points = smoother line
        const timeIncrement = 0.000001 // Very small increment (1 microsecond)
        
        for (let i = 0; i < numPoints; i++) {
          const price = (minPrice - pricePadding) + (maxPrice - minPrice + pricePadding * 2) * (i / (numPoints - 1))
          verticalPoints.push({
            time: earningsTimestamp + (i * timeIncrement),
            value: price,
          })
        }
        
        verticalLineSeries.setData(verticalPoints)
        
        // Store reference to remove later if needed
        if (!tab.earningsLines) {
          tab.earningsLines = []
        }
        tab.earningsLines.push(verticalLineSeries)
      })
    }

    // Add Moving Averages
    const maSeries = {}
    const maConfigs = [
      { key: 'ma13', period: 13, color: '#E1C542', enabled: tab.indicators?.ma13 },
      { key: 'ma50', period: 50, color: '#4AA3DF', enabled: tab.indicators?.ma50 },
      { key: 'ma200', period: 200, color: '#F39C12', enabled: tab.indicators?.ma200 },
      { key: 'ma800', period: 800, color: '#999999', enabled: tab.indicators?.ma800 },
    ]
    
    maConfigs.forEach(config => {
      if (config.enabled && data.some(d => d[config.key] != null)) {
        const maData = data
          .filter(d => d[config.key] != null)
          .map(d => ({
            time: d.time / 1000,
            value: d[config.key]
          }))
        
        if (maData.length > 0) {
          const series = tab.chart.addLineSeries({
            color: config.color,
            lineWidth: 1,
            priceLineVisible: false,
            lastValueVisible: true,
            title: `MA${config.period}`
          })
          series.setData(maData)
          maSeries[config.key] = series
        }
      }
    })
    tab.maSeries = maSeries

    // Add RSI indicator as overlay on main chart
    if (tab.indicators?.rsi && data.some(d => d.rsi != null)) {
      const rsiData = data
        .filter(d => d.rsi != null)
        .map(d => ({
          time: d.time / 1000,
          value: d.rsi
        }))
      
      if (rsiData.length > 0) {
        // Create RSI series with separate price scale on the right
        const rsiSeries = tab.chart.addLineSeries({
          color: '#9c27b0',
          lineWidth: 2,
          priceLineVisible: false,
          lastValueVisible: true,
          title: 'RSI',
          priceScaleId: 'rsi',
        })
        
        // Configure RSI price scale (0-100 range) on right side
        tab.chart.priceScale('rsi').applyOptions({
          scaleMargins: {
            top: 0.1,
            bottom: 0.1,
          },
        })
        
        // Add RSI reference lines (30, 50, 70)
        rsiSeries.createPriceLine({
          price: 30,
          color: '#ef5350',
          lineWidth: 1,
          lineStyle: 1, // Dashed
          axisLabelVisible: true,
          title: 'Oversold',
        })
        rsiSeries.createPriceLine({
          price: 50,
          color: '#888',
          lineWidth: 1,
          lineStyle: 1,
          axisLabelVisible: true,
          title: 'Neutral',
        })
        rsiSeries.createPriceLine({
          price: 70,
          color: '#26a69a',
          lineWidth: 1,
          lineStyle: 1,
          axisLabelVisible: true,
          title: 'Overbought',
        })
        
        rsiSeries.setData(rsiData)
        tab.rsiSeries = rsiSeries
      }
    }

    // Add Bull Run markers
    if (tab.indicators?.bullRun && data.some(d => d.bull_run != null && d.bull_run !== 0)) {
      const bullRunMarkers = []
      data.forEach((d) => {
        if (d.bull_run === 1) {
          // Bull signal
          bullRunMarkers.push({
            time: d.time / 1000,
            position: 'belowBar',
            color: '#26a69a',
            shape: 'arrowUp',
            size: 2,
            text: '🐂',
          })
        } else if (d.bull_run === -1) {
          // Bear signal
          bullRunMarkers.push({
            time: d.time / 1000,
            position: 'aboveBar',
            color: '#ef5350',
            shape: 'arrowDown',
            size: 2,
            text: '🐻',
          })
        }
      })
      
      if (bullRunMarkers.length > 0) {
        // Get existing markers and add bull run markers
        const existingMarkers = tab.chartType === 'Candle' && tab.candlestickSeries
          ? (tab.candlestickSeries.markers() || [])
          : (tab.lineSeries?.markers() || [])
        
        const allMarkers = [...existingMarkers, ...bullRunMarkers]
        
        if (tab.chartType === 'Candle' && tab.candlestickSeries) {
          tab.candlestickSeries.setMarkers(allMarkers)
        } else if (tab.lineSeries) {
          tab.lineSeries.setMarkers(allMarkers)
        }
      }
    }

    tab.chart.timeScale().fitContent()
    
    // Add resize observer to handle container size changes
    if (!tab.resizeObserver) {
      tab.resizeObserver = new ResizeObserver(() => {
        if (tab.chart && chartContainer) {
          const width = chartContainer.clientWidth
          const height = chartContainer.clientHeight
          if (width > 0 && height > 0) {
            tab.chart.applyOptions({ width, height })
          }
        }
      })
      tab.resizeObserver.observe(chartContainer)
    }
    
    // Save indicator settings for this ticker
    if (tab.indicators) {
      saveIndicatorSettings(tab.selectedTicker, tab.indicators)
    }
    
    console.log('Chart loaded successfully for', tab.selectedTicker)
    
    // Update drawing coordinates after chart is fully loaded
    await nextTick()
    updateDrawingCoordinates(tabId)
  } catch (error) {
    console.error('Chart load error:', error)
    console.error('Error details:', {
      message: error.message,
      stack: error.stack,
      ticker: tab.selectedTicker,
      timeframe: tab.timeframe,
      chartType: tab.chartType
    })
  }
}

// Dynamic loading of more historical data when zooming out
const loadMoreHistoricalData = async (tabId) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab || !tab.selectedTicker || !tab.chart || !tab.chartData) return
  
  // Prevent multiple concurrent loads
  if (loadingMoreData.value[tabId]) return
  
  loadingMoreData.value[tabId] = true
  
  try {
    // Fetch extended history (max available)
    console.log('Loading more historical data for', tab.selectedTicker)
    
    const response = await api.getChart({
      ticker: tab.selectedTicker,
      timeframe: tab.timeframe,
      chart_type: tab.chartType.toLowerCase(),
      extend_history: true
    })
    
    const extendedData = response.data
    if (!extendedData?.data?.length) {
      console.log('No additional data available')
      return
    }
    
    // Get existing timestamps
    const existingTimes = new Set(tab.chartData.map(d => d.time))
    
    // Filter new data (only prepend older data)
    const newData = extendedData.data.filter(d => !existingTimes.has(d.time))
    
    if (newData.length === 0) {
      console.log('No new historical data to add')
      tab.historyFullyLoaded = true
      return
    }
    
    console.log(`Adding ${newData.length} new historical data points`)
    
    // Merge data (new data first, then existing)
    const mergedData = [...newData, ...tab.chartData].sort((a, b) => a.time - b.time)
    tab.chartData = mergedData
    
    // Update the chart series
    if (tab.chartType === 'Candle' && tab.candlestickSeries) {
      tab.candlestickSeries.setData(mergedData.map(d => ({
        time: d.time / 1000,
        open: d.open,
        high: d.high,
        low: d.low,
        close: d.close,
      })))
    } else if (tab.lineSeries) {
      const lineData = mergedData.map(d => ({ time: d.time / 1000, value: d.close })).filter(d => !isNaN(d.value))
      if (lineData.length > 0) tab.lineSeries.setData(lineData)
    }
    
    // Update drawings
    updateDrawingCoordinates(tabId)
    
    // Mark as fully loaded if we received all historical data
    if (newData.length < 100) {
      tab.historyFullyLoaded = true
    }
  } catch (error) {
    console.error('Failed to load more historical data:', error)
  } finally {
    loadingMoreData.value[tabId] = false
  }
}

// Check if we need to load more data based on visible range
const checkAndLoadMoreData = (tabId) => {
  const tab = tabs.value.find(t => t && t.id === tabId)
  if (!tab || !tab.chart || !tab.chartData || tab.chartData.length === 0) return
  if (tab.historyFullyLoaded) return // Already loaded all history
  
  const timeScale = tab.chart.timeScale()
  const visibleRange = timeScale.getVisibleLogicalRange()
  
  if (!visibleRange) return
  
  // Get the first bar index in data
  const firstDataTime = tab.chartData[0].time / 1000
  const visibleStartTime = timeScale.coordinateToTime(0)
  
  // If visible range extends before our data, load more
  if (visibleRange.from < 10) { // Near the start of data
    loadMoreHistoricalData(tabId)
  }
}

const formatVolume = (volume) => {
  if (!volume) return '--'
  if (volume >= 1e9) return (volume / 1e9).toFixed(2) + 'B'
  if (volume >= 1e6) return (volume / 1e6).toFixed(2) + 'M'
  if (volume >= 1e3) return (volume / 1e3).toFixed(2) + 'K'
  return volume.toString()
}

const handleSettingsSave = () => {
  // Placeholder for future settings
  showSettings.value = false
}

const openAiDrawModal = () => {
  showAiDrawModal.value = true
  closeChartContextMenu()
}

const getCurrentChartData = () => {
  const tab = tabs.value.find(t => t.id === activeTab.value)
  if (!tab || !tab.candlestickSeries) return []
  
  // Get visible data or recent data
  // We'll try to get the data from the series if possible, or fallback to what we have in memory if we stored it
  // Since we don't strictly store the raw data in the tab object after loading (we pass it to series),
  // we might need to rely on what we can get.
  // For now, let's assume we can't easily get data back from series without keeping a reference.
  // Let's modify loadChart to store data in tab.chartData for this purpose.
  return tab.chartData || []
}

const handleAiDrawingAdded = (drawing) => {
  const tabId = activeTab.value
  const tab = tabs.value.find(t => t.id === tabId)
  if (!tab) return

  if (!tab.drawings) tab.drawings = []
  
  // Ensure drawing has an ID
  if (!drawing.id) drawing.id = Date.now().toString()
  
  tab.drawings.push(drawing)
  updateDrawingCoordinates(tabId)
  saveUserTabs()
  broadcastSharedPatch(tabId, { drawings: tab.drawings })
}
</script>

<style scoped>
.dashboard {
  display: flex;
  flex-direction: column;
  height: 100vh;
  background: var(--surface-0, #0b0e14);
  color: var(--text-primary, #e2e8f0);
  pointer-events: auto;
}

/* Tab Bar - barra full-width moderna senza spazi neri */
.tab-bar-container {
  position: relative;
  z-index: 100;
  pointer-events: auto;
  flex-shrink: 0;
  padding: 0;
}

.tab-bar-container.loading-bar {
  opacity: 0.7;
}

.loading-tabs-placeholder {
  height: 48px;
  width: 100%;
  background: rgba(20, 20, 20, 0.8);
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
}

.tab-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 20px 0 16px;
  background: var(--glass-bg-strong, rgba(15, 23, 42, 0.8));
  backdrop-filter: var(--glass-blur, blur(16px));
  border-bottom: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  height: 56px;
  box-shadow: 0 1px 0 rgba(255, 255, 255, 0.02) inset;
}

.tabs-section {
  display: flex;
  flex: 1;
  gap: 4px;
  height: 100%;
  align-items: center;
  position: relative;
}

.tab-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  gap: 0;
  cursor: move;
  transition: transform 0.2s;
}

.tab-wrapper:hover .tab-close-btn {
  opacity: 1;
}

.tab-wrapper.dragging {
  opacity: 0.5;
  cursor: grabbing;
}

.tab-wrapper.drag-over {
  transform: translateX(4px);
}

.tab-drag-handle {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0 8px;
  margin-right: 4px;
  cursor: grab;
  user-select: none;
  -webkit-user-select: none;
  flex-shrink: 0;
}

.tabs-section .tab-wrapper:first-child .tab-drag-handle {
  padding: 0 4px;
  margin-right: 0;
}

.tabs-section .tab-wrapper:first-child .tab-drag-handle .divider-line {
  opacity: 0;
  width: 0;
  pointer-events: none;
}

.tab-drag-handle .divider-line {
  width: 1px;
  height: 18px;
  background: linear-gradient(180deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.15) 20%, 
    rgba(255, 255, 255, 0.25) 50%, 
    rgba(255, 255, 255, 0.15) 80%, 
    transparent 100%);
  border-radius: 1px;
  transition: all 0.2s ease;
}

.tab-drag-handle:hover .divider-line {
  background: linear-gradient(180deg, 
    transparent 0%, 
    rgba(255, 255, 255, 0.25) 20%, 
    rgba(255, 255, 255, 0.4) 50%, 
    rgba(255, 255, 255, 0.25) 80%, 
    transparent 100%);
  height: 20px;
}

.tab-drag-handle:active {
  cursor: grabbing;
}

.tab-btn {
  padding: 0 18px;
  height: 38px;
  background-color: transparent;
  border: none !important;
  outline: none !important;
  box-shadow: none !important;
  -webkit-appearance: none;
  -moz-appearance: none;
  appearance: none;
  border-radius: var(--radius-sm, 10px);
  color: var(--text-secondary, #94a3b8);
  cursor: pointer;
  font-size: 13px;
  font-weight: 600;
  text-transform: uppercase;
  transition: all 0.2s;
  letter-spacing: 0.6px;
}

.tab-btn:hover {
  color: var(--text-primary, #e2e8f0);
  background-color: rgba(255, 255, 255, 0.06);
}

.tab-btn:focus,
.tab-btn:focus-visible {
  outline: none !important;
  box-shadow: none !important;
}

.tab-btn.active {
  background-color: rgba(255, 255, 255, 0.1);
  color: var(--text-primary, #e2e8f0);
}

.tab-live-pill {
  margin-left: 8px;
  font-size: 10px;
  padding: 2px 6px;
  border-radius: 999px;
  background: rgba(34, 197, 94, 0.2);
  color: #22c55e;
  letter-spacing: 0.06em;
}

.shared-tab-banner {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  margin-bottom: 10px;
  border-radius: 12px;
  background: linear-gradient(135deg, rgba(37, 99, 235, 0.2), rgba(15, 23, 42, 0.9));
  border: 1px solid rgba(59, 130, 246, 0.25);
}

.shared-tab-info {
  display: flex;
  align-items: center;
  gap: 10px;
  color: #e2e8f0;
  font-size: 13px;
}

.shared-tab-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #22c55e;
  box-shadow: 0 0 12px rgba(34, 197, 94, 0.6);
}

.shared-tab-title {
  font-weight: 600;
}

.shared-tab-count {
  color: #94a3b8;
}

.shared-tab-actions {
  display: flex;
  align-items: center;
  gap: 10px;
}

.shared-tab-stop {
  background: rgba(248, 113, 113, 0.2);
  border: 1px solid rgba(248, 113, 113, 0.4);
  color: #fecaca;
  padding: 6px 10px;
  border-radius: 10px;
  font-size: 12px;
  cursor: pointer;
}

.shared-tab-guest {
  font-size: 12px;
  color: #cbd5f5;
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.6);
  backdrop-filter: var(--glass-blur, blur(16px));
  -webkit-backdrop-filter: var(--glass-blur, blur(16px));
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  background: var(--glass-bg, rgba(30, 41, 59, 0.5));
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-lg, 24px);
  box-shadow: var(--shadow-glass, 0 25px 50px -12px rgba(0, 0, 0, 0.5));
  color: var(--text-primary, #e2e8f0);
  max-height: 80vh;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px 20px;
  border-bottom: 1px solid rgba(148, 163, 184, 0.12);
}

.modal-body {
  padding: 16px 20px;
}

.close-btn {
  background: rgba(148, 163, 184, 0.12);
  border: none;
  color: #e2e8f0;
  width: 28px;
  height: 28px;
  border-radius: 8px;
  cursor: pointer;
}

.share-modal {
  width: min(520px, 90vw);
}

.share-hint {
  color: #94a3b8;
  font-size: 13px;
  margin-bottom: 14px;
}

.share-list {
  display: grid;
  gap: 10px;
  margin-bottom: 12px;
}

.share-item {
  text-align: left;
  padding: 12px;
  border-radius: 12px;
  border: 1px solid rgba(148, 163, 184, 0.2);
  background: rgba(15, 23, 42, 0.6);
  color: #e2e8f0;
  cursor: pointer;
  transition: border 0.2s, transform 0.2s;
}

.share-item.selected {
  border-color: rgba(59, 130, 246, 0.8);
  transform: translateY(-1px);
}

.share-item-title {
  font-weight: 600;
}

.share-item-type {
  font-size: 12px;
  color: #94a3b8;
  margin-top: 4px;
}

.share-empty {
  color: #64748b;
  font-size: 13px;
  padding: 12px;
  border-radius: 10px;
  background: rgba(15, 23, 42, 0.6);
  border: 1px dashed rgba(148, 163, 184, 0.2);
}

.share-error {
  color: #f87171;
  font-size: 12px;
  margin-top: 8px;
}

.tab-share-btn {
  border: none;
  border-radius: 10px;
  padding: 8px 12px;
  font-size: 12px;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s, background 0.2s;
}

.tab-share-btn.primary {
  background: #2563eb;
  color: #f8fafc;
  box-shadow: 0 12px 24px rgba(37, 99, 235, 0.35);
}

.tab-share-btn.primary:hover {
  transform: translateY(-1px);
}

.tab-share-btn.ghost {
  background: rgba(148, 163, 184, 0.15);
  color: #e2e8f0;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
  padding: 16px 20px 20px;
  border-top: 1px solid rgba(148, 163, 184, 0.12);
}

.tab-rename-input {
  background: rgba(255, 255, 255, 0.08);
  border: 1px solid rgba(66, 153, 225, 0.6);
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  padding: 0 8px;
  margin: 0;
  width: 100px;
  border-radius: 6px;
  text-transform: uppercase;
  letter-spacing: 1px;
  outline: none;
  font-family: inherit;
}

.tab-close-btn {
  position: absolute;
  right: 6px;
  top: 50%;
  transform: translateY(-50%);
  background: rgba(255, 255, 255, 0.1);
  border: none;
  border-radius: 50%;
  width: 18px;
  height: 18px;
  color: #aaa;
  font-size: 14px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 10;
  padding: 0;
  line-height: 1;
  transition: all 0.2s ease;
}

.tab-close-btn:hover {
  background: rgba(244, 67, 54, 1);
  color: #fff;
  transform: translateY(-50%) scale(1.1);
}

.add-tab-btn {
  padding: 0 16px;
  height: 36px;
  background-color: rgba(255, 255, 255, 0.04);
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: 10px;
  color: #9ca3af;
  cursor: pointer;
  font-size: 18px;
  font-weight: 400;
  margin-left: 8px;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  line-height: 1;
}

.add-tab-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #fff;
  border-color: rgba(255, 255, 255, 0.12);
}

/* Tab Content - stacking context per evitare che chart/overlay blocchino i tab */
.tab-content {
  flex: 1;
  overflow: hidden;
  position: relative;
  z-index: 0;
  isolation: isolate;
}

.tab-panel {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  width: 100%;
  height: 100%;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.stocks-panel, .earnings-panel, .news-panel, .bot-panel, .backtesting-panel, .flex-panel {
  height: 100%;
}

/* Main Content Layout for Stocks Tab */
.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  min-height: 0; /* Important for flex scrolling */
}

/* Chart Info Bar */
.chart-info-bar {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 12px 24px;
  background: rgba(0, 0, 0, 0.2);
  border-bottom: 1px solid var(--glass-border, rgba(255, 255, 255, 0.05));
  flex-wrap: nowrap;
  overflow-x: auto;
}

.chart-info-bar::-webkit-scrollbar {
  display: none;
}

/* Ticker Identity */
.info-ticker {
  display: flex;
  align-items: baseline;
  gap: 10px;
  flex-shrink: 0;
}

.info-ticker .ticker-symbol {
  font-size: 20px;
  font-weight: 700;
  color: #fff;
  letter-spacing: 0.5px;
}

.info-ticker .ticker-name {
  font-size: 12px;
  color: rgba(255, 255, 255, 0.5);
  max-width: 150px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* Main Price Display */
.info-price-main {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.info-price-main .main-price {
  font-size: 24px;
  font-weight: 700;
  color: var(--text-primary, #e2e8f0);
  font-family: 'Roboto Mono', monospace;
}

.info-price-main .main-price.positive {
  color: var(--accent-gain, #34d399);
}

.info-price-main .main-price.negative {
  color: var(--accent-loss, #f43f5e);
}

.info-price-main .price-change {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.info-price-main .change-value {
  font-size: 13px;
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;
  color: rgba(255, 255, 255, 0.6);
}

.info-price-main .change-value.positive {
  color: var(--accent-gain, #34d399);
}

.info-price-main .change-value.negative {
  color: var(--accent-loss, #f43f5e);
}

.info-price-main .change-percent {
  font-size: 11px;
  font-family: 'Roboto Mono', monospace;
  color: rgba(255, 255, 255, 0.4);
}

.info-price-main .change-percent.positive {
  color: rgba(52, 211, 153, 0.8);
}

.info-price-main .change-percent.negative {
  color: rgba(244, 63, 94, 0.8);
}

.market-badge {
  padding: 3px 8px;
  border-radius: 4px;
  font-size: 9px;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.market-badge.regular {
  background: rgba(38, 166, 154, 0.2);
  color: #26a69a;
  animation: pulse-live 2s infinite;
}

.market-badge.post {
  background: rgba(156, 39, 176, 0.2);
  color: #ce93d8;
}

.market-badge.pre {
  background: rgba(255, 152, 0, 0.2);
  color: #ffb74d;
}

.market-badge.closed,
.market-badge.postpost,
.market-badge.prepre {
  background: rgba(255, 255, 255, 0.08);
  color: rgba(255, 255, 255, 0.5);
}

@keyframes pulse-live {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

/* Extended Hours */
.info-extended-hours {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px;
  background: rgba(156, 39, 176, 0.1);
  border: 1px solid rgba(156, 39, 176, 0.2);
  border-radius: 6px;
  flex-shrink: 0;
}

.info-extended-hours .extended-label {
  font-size: 9px;
  font-weight: 700;
  color: #ce93d8;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.info-extended-hours .extended-price {
  font-size: 15px;
  font-weight: 600;
  font-family: 'Roboto Mono', monospace;
  color: #fff;
}

.info-extended-hours .extended-price.positive {
  color: #26a69a;
}

.info-extended-hours .extended-price.negative {
  color: #ef5350;
}

.info-extended-hours .extended-change {
  font-size: 11px;
  font-family: 'Roboto Mono', monospace;
  color: rgba(255, 255, 255, 0.5);
}

.info-extended-hours .extended-change.positive {
  color: rgba(38, 166, 154, 0.8);
}

.info-extended-hours .extended-change.negative {
  color: rgba(239, 83, 80, 0.8);
}

/* OHLC Data */
.info-ohlc {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-left: auto;
  flex-shrink: 0;
}

.ohlc-item {
  display: flex;
  align-items: center;
  gap: 4px;
}

.ohlc-item .ohlc-label {
  font-size: 10px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.35);
  text-transform: uppercase;
}

.ohlc-item .ohlc-value {
  font-size: 12px;
  font-weight: 500;
  font-family: 'Roboto Mono', monospace;
  color: rgba(255, 255, 255, 0.7);
}

.ohlc-item .ohlc-value.high {
  color: #26a69a;
}

.ohlc-item .ohlc-value.low {
  color: #ef5350;
}

.price-value {
  font-size: 36px;
  font-weight: 700;
  color: #fff;
  font-family: 'Roboto Mono', monospace;
  letter-spacing: -1px;
  text-shadow: 0 0 15px rgba(255, 255, 255, 0.3);
  line-height: 1;
}

/* Chart Toolbar */
.chart-toolbar {
  position: relative;
  z-index: 2;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 12px 32px;
  background-color: rgba(0, 0, 0, 0.1);
  border-bottom: 1px solid var(--glass-border, rgba(255, 255, 255, 0.05));
  flex-shrink: 0;
  pointer-events: auto;
}

.timeframe-buttons, .chart-type-buttons {
  display: flex;
  background-color: #151515;
  border-radius: 4px;
  padding: 2px;
}

.timeframe-btn, .chart-type-btn {
  padding: 4px 10px;
  background-color: transparent;
  border: none;
  border-radius: 2px;
  color: #777;
  cursor: pointer;
  font-size: 10px;
  font-weight: 600;
  transition: all 0.2s;
}

.timeframe-btn:hover, .chart-type-btn:hover {
  color: #fff;
}

.timeframe-btn.active, .chart-type-btn.active {
  background-color: #333;
  color: #fff;
  box-shadow: 0 1px 3px rgba(0,0,0,0.5);
}

.indicators-buttons {
  display: flex;
  gap: 4px;
  margin-left: 12px;
}

.indicator-btn {
  padding: 4px 8px;
  background-color: #121212;
  border: 1px solid #2a2a2a;
  border-radius: 2px;
  color: #777;
  cursor: pointer;
  font-size: 10px;
  font-weight: 600;
  transition: all 0.2s;
  text-transform: uppercase;
}

.indicator-btn:hover {
  border-color: #555;
  color: #fff;
}

.indicator-btn.active {
  background-color: #fff;
  color: #000;
  border-color: #fff;
}

.toolbar-actions {
  display: flex;
  gap: 6px;
  margin-left: auto;
}

.settings-btn {
  padding: 8px;
  background-color: transparent;
  border: none;
  color: #666;
  cursor: pointer;
  font-size: 16px;
  transition: color 0.2s;
}

.settings-btn:hover {
  color: #fff;
}

/* Panels */
.left-panel {
  width: 280px;
  background-color: rgba(11, 14, 20, 0.5);
  backdrop-filter: var(--glass-blur, blur(16px));
  -webkit-backdrop-filter: var(--glass-blur, blur(16px));
  border-right: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  padding: 24px;
  display: flex;
  flex-direction: column;
  height: 100%;
  overflow: hidden;
}

.search-section {
  margin-bottom: 20px;
  position: relative;
}

.search-input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  gap: 8px;
}

.search-input {
  flex: 1;
  padding: 12px 16px;
  background-color: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--glass-border, rgba(255, 255, 255, 0.1));
  border-radius: var(--radius-sm, 12px);
  color: var(--text-primary, #e2e8f0);
  font-size: 13px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  cursor: text;
  font-family: 'Roboto Mono', monospace;
  letter-spacing: 0.3px;
}

.search-input::placeholder {
  color: var(--text-secondary, #94a3b8);
  transition: color 0.3s;
}

.search-input:focus {
  outline: none;
  border-color: #4299e1;
  background-color: #111;
  box-shadow: 0 0 0 3px rgba(66, 153, 225, 0.1);
  transform: translateY(-1px);
}

.search-input:focus::placeholder {
  color: #777;
}

.search-input-glow {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  border-radius: 6px;
  opacity: 0;
  background: linear-gradient(135deg, rgba(66, 153, 225, 0.1), rgba(139, 92, 246, 0.1));
  pointer-events: none;
  transition: opacity 0.3s ease;
  z-index: -1;
}

.search-input-glow.active {
  opacity: 1;
  animation: pulse-glow 2s ease-in-out infinite;
}

@keyframes pulse-glow {
  0%, 100% {
    opacity: 0.3;
  }
  50% {
    opacity: 0.6;
  }
}

.add-btn {
  padding: 10px 14px;
  background-color: #1a1a1a;
  border: 2px solid #333;
  border-radius: 6px;
  color: #666;
  cursor: not-allowed;
  font-size: 16px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 44px;
  height: 44px;
}

.add-btn.enabled {
  background-color: #4299e1;
  border-color: #4299e1;
  color: #fff;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(66, 153, 225, 0.3);
}

.add-btn.enabled:hover {
  background-color: #3182ce;
  border-color: #3182ce;
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(66, 153, 225, 0.4);
}

.add-btn.enabled:active {
  transform: translateY(0);
  box-shadow: 0 2px 8px rgba(66, 153, 225, 0.3);
}

.add-icon {
  display: block;
  transition: transform 0.2s;
}

.add-btn.enabled:hover .add-icon {
  transform: scale(1.2);
}

/* Search Results */
.search-loading {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 16px;
  color: #888;
  font-size: 13px;
  justify-content: center;
}

.loading-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #333;
  border-top-color: #4299e1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

.tabs-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 400px;
}

.tabs-loading .loading-spinner {
  width: 40px;
  height: 40px;
  border-width: 3px;
}

@keyframes spin {
  to {
    transform: rotate(360deg);
  }
}

.search-no-results {
  padding: 24px 16px;
  text-align: center;
  color: #666;
}

.no-results-icon {
  font-size: 32px;
  display: block;
  margin-bottom: 8px;
  opacity: 0.5;
}

.search-no-results p {
  margin: 4px 0;
  font-size: 13px;
}

.no-results-hint {
  font-size: 11px;
  color: #555;
}

.search-results {
  margin-top: 8px;
  max-height: 300px;
  overflow-y: auto;
  overflow-x: hidden;
  border-radius: 6px;
  background-color: #0a0a0a;
  border: 1px solid #222;
}

/* Custom scrollbar for search results */
.search-results::-webkit-scrollbar {
  width: 6px;
}

.search-results::-webkit-scrollbar-track {
  background: #0a0a0a;
  border-radius: 3px;
}

.search-results::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 3px;
  transition: background 0.2s;
}

.search-results::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.search-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #1a1a1a;
  cursor: pointer;
  transition: all 0.2s cubic-bezier(0.4, 0, 0.2, 1);
  position: relative;
  background-color: #0a0a0a;
}

.search-result-item:last-child {
  border-bottom: none;
}

.search-result-item::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 3px;
  background-color: transparent;
  transition: background-color 0.2s;
}

.search-result-item:hover,
.search-result-item.hovered {
  background-color: #111;
  padding-left: 20px;
  transform: translateX(4px);
}

.search-result-item:hover::before,
.search-result-item.hovered::before {
  background-color: #4299e1;
}

.search-result-item.selected {
  background-color: #1a1a1a;
  border-left: 3px solid #4299e1;
  padding-left: 13px;
}

.result-main {
  flex: 1;
  min-width: 0;
}

.result-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
  flex-wrap: wrap;
}

.result-symbol {
  font-weight: 700;
  color: #fff;
  font-size: 14px;
  letter-spacing: 0.5px;
  font-family: 'Roboto Mono', monospace;
}

.asset-type-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 12px;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
  transition: all 0.2s;
}

.asset-type-badge.type-equity {
  background-color: rgba(66, 153, 225, 0.15);
  color: #4299e1;
  border: 1px solid rgba(66, 153, 225, 0.3);
}

.asset-type-badge.type-etf {
  background-color: rgba(139, 92, 246, 0.15);
  color: #8b5cf6;
  border: 1px solid rgba(139, 92, 246, 0.3);
}

.asset-type-badge.type-crypto {
  background-color: rgba(251, 191, 36, 0.15);
  color: #fbbf24;
  border: 1px solid rgba(251, 191, 36, 0.3);
}

.asset-type-badge.type-future {
  background-color: rgba(236, 72, 153, 0.15);
  color: #ec4899;
  border: 1px solid rgba(236, 72, 153, 0.3);
}

.asset-type-badge.type-index {
  background-color: rgba(34, 197, 94, 0.15);
  color: #22c55e;
  border: 1px solid rgba(34, 197, 94, 0.3);
}

.asset-type-badge.type-option {
  background-color: rgba(245, 158, 11, 0.15);
  color: #f59e0b;
  border: 1px solid rgba(245, 158, 11, 0.3);
}

.asset-type-badge.type-currency {
  background-color: rgba(168, 85, 247, 0.15);
  color: #a855f7;
  border: 1px solid rgba(168, 85, 247, 0.3);
}

.asset-type-badge.type-default {
  background-color: rgba(107, 114, 128, 0.15);
  color: #6b7280;
  border: 1px solid rgba(107, 114, 128, 0.3);
}

.result-details {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.result-name {
  font-size: 12px;
  color: #888;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  flex: 1;
  min-width: 0;
}

.result-exchange {
  font-size: 10px;
  color: #666;
  font-family: 'Roboto Mono', monospace;
  padding: 2px 6px;
  background-color: #1a1a1a;
  border-radius: 4px;
}

.result-action {
  display: flex;
  align-items: center;
  opacity: 0;
  transition: opacity 0.2s;
}

.search-result-item:hover .result-action,
.search-result-item.hovered .result-action {
  opacity: 1;
}

.add-hint {
  font-size: 10px;
  color: #4299e1;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.watchlist-sections {
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
  min-height: 0;
  overflow: hidden;
}

.watchlist-section {
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.watchlist-section.watchlist-main {
  flex: 2;
  min-height: 0;
}

.watchlist-section.bot-section {
  flex: 1;
  min-height: 0;
  border-top: 1px solid #222;
  padding-top: 12px;
  margin-top: 4px;
}

.bot-section-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  cursor: pointer;
  user-select: none;
}

.bot-section-header .panel-title {
  margin-bottom: 0;
  padding-bottom: 0;
  border-bottom: none;
}

.bot-section-header .bot-tick-checkbox {
  cursor: pointer;
  accent-color: #4299e1;
  flex-shrink: 0;
}

.bot-section .remove-btn {
  display: none;
}

.bot-empty {
  font-size: 11px;
  color: #555;
  padding: 12px;
  text-align: center;
}

.panel-title {
  font-size: 11px;
  font-weight: 700;
  text-transform: uppercase;
  color: #666;
  letter-spacing: 1px;
  margin-bottom: 15px;
  padding-bottom: 5px;
  border-bottom: 1px solid #222;
}

.watchlist {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  margin-bottom: 15px;
  min-height: 0;
  max-height: 100%;
}

/* Custom scrollbar for watchlist */
.watchlist::-webkit-scrollbar {
  width: 6px;
}

.watchlist::-webkit-scrollbar-track {
  background: #0a0a0a;
  border-radius: 3px;
}

.watchlist::-webkit-scrollbar-thumb {
  background: #333;
  border-radius: 3px;
  transition: background 0.2s;
}

.watchlist::-webkit-scrollbar-thumb:hover {
  background: #555;
}

.watchlist-item {
  padding: 12px 10px;
  border-bottom: 1px solid #1a1a1a;
  cursor: pointer;
  transition: background-color 0.2s;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.watchlist-item:hover {
  background-color: #111;
}

.watchlist-item.active {
  background-color: #1a1a1a;
  border-left: 3px solid #4299e1; /* Blue accent for better visibility */
  padding-left: 7px; /* Adjust padding to compensate for border */
}

.symbol {
  font-weight: 700;
  color: #fff;
  font-size: 14px;
  letter-spacing: 0.5px;
}

.watchlist-item.active .symbol {
  color: #4299e1; /* Highlight symbol when active */
}

.name {
  font-size: 11px;
  color: #666;
  text-align: right;
  font-family: 'Roboto Mono', monospace;
}

.watchlist-item.active .name {
  color: #888;
}

.remove-btn {
  width: 100%;
  padding: 12px;
  background-color: transparent;
  border: 1px solid #333;
  border-radius: 2px;
  color: #666;
  font-size: 11px;
  text-transform: uppercase;
  letter-spacing: 1px;
  cursor: pointer;
  transition: all 0.2s;
  margin-top: auto; /* Push to bottom if parent is flex column */
}

.remove-btn:hover {
  border-color: #f44336;
  color: #f44336;
  background-color: rgba(244, 67, 54, 0.05);
}

.chart-container {
  flex: 1;
  background: var(--glass-bg, rgba(30, 41, 59, 0.3));
  position: relative;
  min-width: 0;
  min-height: 0;
  overflow: hidden;
  backdrop-filter: var(--glass-blur, blur(16px));
  -webkit-backdrop-filter: var(--glass-blur, blur(16px));
}

.chart-wrapper {
  width: 100%;
  height: 100%;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}


.welcome-screen {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
  cursor: pointer;
  user-select: none;
  outline: none;
}
.welcome-screen:focus-visible {
  outline: 2px solid rgba(66, 153, 225, 0.6);
  outline-offset: 4px;
}
.welcome-screen-hint {
  margin-top: 12px;
  font-size: 12px;
  color: #555;
}

.welcome-screen h1 {
  font-weight: 300;
  letter-spacing: 2px;
  text-transform: uppercase;
  font-size: 24px;
  margin-bottom: 15px;
}

.welcome-screen p {
  color: #666;
  font-size: 13px;
  letter-spacing: 0.5px;
}

/* Custom overrides for lightweight charts */
:deep(.tv-lightweight-charts) {
  font-family: 'Roboto Mono', monospace !important;
}

/* Backdrop per chiudere menu contestuali cliccando fuori */
.context-menu-backdrop {
  position: fixed;
  inset: 0;
  z-index: 10000;
  background: transparent;
  cursor: default;
}

/* Context Menu */
.context-menu {
  position: fixed;
  background-color: #0a0a0a;
  border: 1px solid #333;
  border-radius: 2px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.5);
  z-index: 10001;
  min-width: 120px;
  padding: 4px 0;
}

.context-menu-item {
  width: 100%;
  padding: 10px 16px;
  background: none;
  border: none;
  color: #ccc;
  font-size: 13px;
  text-align: left;
  cursor: pointer;
  transition: all 0.2s;
}

.context-menu-item:hover {
  background-color: #1a1a1a;
  color: #fff;
}

/* AI Analysis Input */
.ai-analysis-input {
  position: relative;
  display: flex;
  align-items: center;
  margin-left: 20px;
  width: 250px;
}

.ai-input {
  width: 100%;
  padding: 6px 12px;
  padding-right: 30px; /* Space for spinner */
  background-color: #151515;
  border: 1px solid #333;
  border-radius: 2px;
  color: #fff;
  font-size: 11px;
  font-family: 'Roboto Mono', monospace;
  transition: all 0.2s;
}

.ai-input:focus {
  outline: none;
  border-color: #4299e1;
  background-color: #1a1a1a;
}

.ai-input::placeholder {
  color: #555;
}

.ai-input:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.ai-loading-spinner {
  position: absolute;
  right: 8px;
  width: 12px;
  height: 12px;
  border: 2px solid #333;
  border-top-color: #4299e1;
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

/* Drawing Overlay */
.chart-container {
  position: relative;
}

.drawing-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 10;
}

.drawing-overlay .drawing-element {
  pointer-events: auto;
  cursor: pointer;
  transition: filter 0.15s ease;
}

.drawing-overlay .drawing-element:hover {
  filter: brightness(1.15);
}

.drawing-overlay .drawing-element.selected {
  filter: brightness(1.25) drop-shadow(0 0 4px rgba(33, 150, 243, 0.6));
  outline: none;
}

.drawing-overlay rect.drawing-element {
  vector-effect: non-scaling-stroke;
}

.temp-drawing {
  opacity: 0.5;
  pointer-events: none !important;
}

/* Drawing Properties Panel */
.drawing-properties-panel {
  position: absolute;
  right: 16px;
  top: 50%;
  transform: translateY(-50%);
  z-index: 1001;
  min-width: 200px;
  background: #1e1e1e;
  border: 1px solid #333;
  border-radius: 8px;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
  overflow: hidden;
}

.drawing-properties-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  background: #252525;
  border-bottom: 1px solid #333;
  font-size: 12px;
  font-weight: 600;
  color: #e0e0e0;
}

.drawing-props-close {
  background: none;
  border: none;
  color: #888;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  padding: 0 4px;
  border-radius: 4px;
}

.drawing-props-close:hover {
  color: #fff;
  background: #333;
}

.drawing-properties-body {
  padding: 12px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.drawing-prop-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.drawing-prop-row label {
  font-size: 11px;
  color: #888;
  font-weight: 600;
}

.drawing-color-input {
  width: 100%;
  height: 32px;
  border: 1px solid #333;
  border-radius: 4px;
  background: #151515;
  cursor: pointer;
  padding: 2px;
}

.drawing-thickness-slider {
  width: 100%;
  accent-color: #2196F3;
}

.drawing-text-edit {
  display: flex;
  gap: 6px;
  align-items: center;
}

.drawing-text-input {
  flex: 1;
  padding: 6px 8px;
  background: #151515;
  border: 1px solid #333;
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
}

.drawing-text-input:focus {
  outline: none;
  border-color: #2196F3;
}

.drawing-edit-btn {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  background: #252525;
  border: 1px solid #333;
  border-radius: 4px;
  color: #aaa;
  cursor: pointer;
  font-size: 14px;
}

.drawing-edit-btn:hover {
  background: #333;
  color: #fff;
}

.drawing-prop-actions {
  margin-top: 4px;
  padding-top: 8px;
  border-top: 1px solid #333;
}

.drawing-delete-btn {
  width: 100%;
  padding: 8px 12px;
  background: rgba(239, 83, 80, 0.15);
  border: 1px solid #d32f2f;
  border-radius: 4px;
  color: #ef5350;
  font-size: 12px;
  cursor: pointer;
  transition: background 0.2s, color 0.2s;
}

.drawing-delete-btn:hover {
  background: rgba(239, 83, 80, 0.25);
  color: #fff;
}

/* (Duplicate .context-menu and .context-menu-item removed — see definition near line 4955) */

.color-picker-section {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 16px;
}

.color-picker-section label {
  font-size: 12px;
  color: #888;
  font-weight: 600;
}

.color-input {
  width: 40px;
  height: 30px;
  border: 1px solid #333;
  border-radius: 4px;
  background: transparent;
  cursor: pointer;
}

.color-input::-webkit-color-swatch-wrapper {
  padding: 2px;
}

.color-input::-webkit-color-swatch {
  border: none;
  border-radius: 2px;
}

.menu-divider {
  height: 1px;
  background-color: #333;
  margin: 4px 0;
}

/* Responsive Dashboard Styles */
@media (max-width: 768px) {
  .dashboard {
    height: 100vh;
    overflow: hidden;
  }

  /* Tab Bar */
  .tab-bar-container {
    padding: 0;
  }

  .tab-bar {
    padding: 0 12px 0 10px;
    height: 52px;
  }

  .tabs-section {
    overflow-x: auto;
    overflow-y: hidden;
    mask-image: linear-gradient(to right, black 85%, transparent 100%);
    -webkit-mask-image: linear-gradient(to right, black 85%, transparent 100%);
    padding-right: 20px;
  }
  
  .tab-btn {
    padding: 0 12px;
    font-size: 12px;
    white-space: nowrap;
    height: 100%;
  }

  .add-tab-btn {
    display: none; /* Hide add button on mobile for now */
  }

  /* Main Content Layout */
  .main-content {
    flex-direction: column;
    position: relative;
  }

  /* Left Panel (Watchlist) */
  .left-panel {
    position: absolute;
    top: 0;
    left: 0;
    bottom: 0;
    width: 85%; /* Drawer width */
    max-width: 320px;
    z-index: 100;
    background-color: #0c0c0c;
    transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 4px 0 20px rgba(0,0,0,0.6);
    border-right: 1px solid #222;
  }

  .left-panel.active {
    transform: translateX(0);
  }
  
  .mobile-close-btn {
    position: absolute;
    top: 10px;
    right: 10px;
    background: #222;
    border: none;
    color: #fff;
    width: 30px;
    height: 30px;
    border-radius: 50%;
    font-size: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 10;
  }

  .mobile-close-btn {
    display: flex;
  }

  .mobile-watchlist-toggle {
    display: inline-flex;
    padding: 6px 12px;
    background: #333;
    border: none;
    border-radius: 4px;
    color: white;
    font-size: 11px;
    font-weight: 600;
    margin-left: 8px;
  }

  /* Chart Container */
  .chart-container {
    width: 100%;
    height: 100%;
  }

  /* Chart Info Bar */
  .chart-info-bar {
    padding: 10px 15px;
    gap: 15px;
    overflow-x: auto;
    white-space: nowrap;
    -webkit-overflow-scrolling: touch;
    scrollbar-width: none;
    border-bottom: 1px solid #222;
    background-color: #000;
  }
  
  .chart-info-bar::-webkit-scrollbar {
    display: none;
  }

  .info-item {
    flex-shrink: 0;
  }
  
  .info-item label {
    font-size: 9px;
  }
  
  .info-value {
    font-size: 13px;
  }
  
  .price-item {
    padding-left: 15px;
    margin-left: 0;
    position: sticky;
    right: 0;
    background: #000;
    border-left: 1px solid #222;
    padding-right: 5px;
    z-index: 2;
  }
  
  .price-value {
    font-size: 20px;
  }

  /* Chart Toolbar */
  .chart-toolbar {
    padding: 8px 10px;
    gap: 10px;
    overflow-x: auto;
    -webkit-overflow-scrolling: touch;
    background-color: #0a0a0a;
  }
  
  .timeframe-buttons, .chart-type-buttons, .indicators-buttons {
    flex-shrink: 0;
  }
  
  .indicator-btn, .timeframe-btn, .chart-type-btn {
    padding: 6px 10px;
    font-size: 11px;
  }
  
  .ai-analysis-input {
    min-width: 180px;
  }
  
  /* Hide desktop-only elements or adjust */
  .add-btn .add-icon {
    font-size: 12px;
  }

  /* Tab panels full height on mobile */
  .tab-panel {
    min-height: 0;
    overflow: auto;
    -webkit-overflow-scrolling: touch;
  }

  .flex-panel,
  .news-panel,
  .bot-panel,
  .earnings-panel,
  .backtesting-panel {
    overflow: auto;
    -webkit-overflow-scrolling: touch;
  }

  /* Context menu: keep on screen */
  .context-menu {
    max-width: min(260px, calc(100vw - 24px));
  }

  /* Drawing properties panel on mobile: full width bottom sheet style */
  .drawing-properties-panel {
    right: 8px;
    left: 8px;
    top: auto;
    bottom: 16px;
    transform: none;
    min-width: 0;
    width: auto;
  }
}

/* Small mobile */
@media (max-width: 480px) {
  .tab-bar-container {
    padding: 6px 8px 0;
  }

  .tab-bar {
    height: 44px;
    padding: 0 8px;
  }

  .tab-btn {
    padding: 0 10px;
    font-size: 11px;
  }

  .tab-drag-handle {
    padding: 0 4px;
    font-size: 10px;
  }

  .left-panel {
    width: 92%;
    max-width: none;
  }

  .chart-info-bar {
    padding: 8px 12px;
    gap: 10px;
  }

  .info-value {
    font-size: 12px;
  }

  .price-value {
    font-size: 18px;
  }

  .chart-toolbar {
    padding: 6px 8px;
    gap: 8px;
    flex-wrap: wrap;
  }

  .indicators-buttons {
    margin-left: 0;
    flex-wrap: wrap;
  }

  .indicator-btn,
  .timeframe-btn,
  .chart-type-btn {
    padding: 6px 8px;
    font-size: 10px;
  }

  .mobile-watchlist-toggle {
    font-size: 10px;
    padding: 6px 10px;
  }
}

/* Default state for desktop */
.mobile-close-btn, .mobile-watchlist-toggle {
  display: none;
}

</style>
