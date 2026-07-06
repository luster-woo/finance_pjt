<template>
  <main class="layout">
    <aside>
      <h1>주변 은행 찾기</h1>
      
      <div class="region-select-group">
        <select v-model="selectedSido" @change="selectedSigungu = ''">
          <option value="">시/도 선택</option>
          <option v-for="sido in Object.keys(regionData)" :key="sido" :value="sido">
            {{ sido }}
          </option>
        </select>

        <select v-model="selectedSigungu" :disabled="!selectedSido">
          <option value="">시/군/구 선택</option>
          <option v-for="sigungu in currentSigunguList" :key="sigungu" :value="sigungu">
            {{ sigungu }}
          </option>
        </select>
      </div>
      
      <div class="search-box">
        <input 
          v-model.trim="keyword" 
          @keyup.enter="searchBanks" 
          placeholder="특정 은행명 (선택사항, 예: 우리은행)" 
        />
        <button @click="searchBanks" class="search-btn">검색</button>
      </div>

      <button class="locate-btn" @click="locate">내 현재 위치로 이동</button>
      
      <p v-if="loading" class="status-msg">불러오는 중...</p>
      <p v-else-if="error" class="error status-msg">{{error}}</p>
      
      <!-- 은행 목록 (은행 미선택 시) -->
      <template v-if="!selectedBank">
        <div class="bank-results">
          <div class="results-header">
            <strong>검색 결과</strong>
            <span>{{ banks.length }}곳</span>
          </div>
          <div class="bank-list">
            <article
              v-for="bank in banks"
              :key="bank.id"
              :class="{ selected: selectedBankId === bank.id }"
              @click="focusBank(bank)"
              style="cursor:pointer"
            >
              <b>{{bank.bank_name}}</b>
              <p>{{bank.address}}</p>
              <small>{{bank.phone || '전화번호 없음'}}</small>
            </article>
            <p v-if="!loading && !error && banks.length === 0" class="empty-result">
              지도에서 지역을 선택해 은행을 검색해 보세요.
            </p>
          </div>
        </div>
      </template>

      <!-- 경로 안내 패널 (은행 선택 시 사이드바를 대체) -->
      <template v-else>
        <div class="route-sidebar">
          <button class="back-to-list" @click="selectedBank = null; selectedBankId = null; clearRoute()">
            ← 목록으로
          </button>

          <!-- 목적지 은행 -->
          <div class="dest-bank-card">
            <strong>{{ selectedBank.bank_name }}</strong>
            <p>{{ selectedBank.address }}</p>
            <small>{{ selectedBank.phone || '전화번호 없음' }}</small>
          </div>

          <div class="route-divider"></div>

          <!-- 출발지 설정 -->
          <p class="route-label">출발지 선택</p>
          <div class="origin-mode-tabs">
            <button class="origin-tab" :class="{ active: originMode === 'gps' }" @click="setOriginMode('gps')">
              📍 현재 위치
            </button>
            <button class="origin-tab" :class="{ active: originMode === 'pick', picking: pickingOrigin }" @click="setOriginMode('pick')">
              🗺 지도에서 선택
            </button>
          </div>

          <p v-if="originMode === 'pick' && pickingOrigin" class="pick-hint">
            👆 지도에서 출발지를 클릭하세요
          </p>
          <p v-else-if="originMode === 'pick' && currentOrigin" class="pick-confirmed">
            ✓ 출발지가 지정됐습니다
          </p>

          <!-- 경로 표시 -->
          <div class="route-flow">
            <div class="flow-row">
              <span class="flow-dot origin-dot"></span>
              <span class="flow-label">{{ originMode === 'gps' ? '내 현재 위치' : (currentOrigin ? '지정한 출발지' : '출발지 미지정') }}</span>
            </div>
            <div class="flow-line">
              <span v-if="routeInfo" class="flow-meta">🚗 {{ formatDist(routeInfo.distance) }} &nbsp;⏱ {{ formatDur(routeInfo.duration) }}</span>
            </div>
            <div class="flow-row">
              <span class="flow-dot dest-dot"></span>
              <span class="flow-label">{{ selectedBank.bank_name }}</span>
            </div>
          </div>

          <p v-if="routeError" class="route-error">{{ routeError }}</p>

          <button
            class="route-go-btn"
            :disabled="routeLoading || (originMode === 'pick' && !currentOrigin)"
            @click="drawRoute"
          >
            {{ routeLoading ? '경로 탐색 중...' : routeInfo ? '↻ 다시 탐색' : '🚗 경로 안내 시작' }}
          </button>
          <button v-if="routeInfo" class="route-clear-btn" @click="clearRoute">
            경로 지우기
          </button>
        </div>
      </template>
    </aside>

    <div class="map-wrap">
      <div id="map"></div>
      <button v-if="isMapMoved" class="research-btn" @click="searchInCurrentArea">
        ↻ 이 지역에서 재검색
      </button>
    </div>
  </main>
</template>

<script setup>
/* global kakao */
import { onMounted, ref, computed, shallowRef } from 'vue';
import { api } from '@/api';

const banks = ref([]);
const loading = ref(false);
const error = ref('');
const map = shallowRef(null);
const markers = [];
const isMapMoved = ref(false);
const selectedBankId = ref(null);
const selectedBank = ref(null);
let myLocationOverlay = null;

// 경로 안내
const routeLoading = ref(false);
const routeError = ref('');
const routeInfo = ref(null);
let routePolyline = ref(null);
const currentOrigin = ref(null);    // { lat, lng }
const originMode = ref('gps');      // 'gps' | 'pick'
const pickingOrigin = ref(false);   // 지도 클릭 대기 중
let originMarker = null;
let pickClickListener = null;       // 카카오맵 클릭 이벤트 핸들러

function formatDist(m) {
  return m >= 1000 ? (m / 1000).toFixed(1) + 'km' : m + 'm';
}
function formatDur(sec) {
  const m = Math.round(sec / 60);
  return m >= 60 ? Math.floor(m / 60) + '시간 ' + (m % 60) + '분' : m + '분';
}

function removePick() {
  if (pickClickListener) {
    kakao.maps.event.removeListener(map.value, 'click', pickClickListener);
    pickClickListener = null;
  }
  pickingOrigin.value = false;
}

function setOriginMode(mode) {
  originMode.value = mode;
  currentOrigin.value = null;
  clearRoute();

  if (mode === 'pick') {
    // 지도 클릭 대기 시작
    pickingOrigin.value = true;
    pickClickListener = (mouseEvent) => {
      const latlng = mouseEvent.latLng;
      currentOrigin.value = { lat: latlng.getLat(), lng: latlng.getLng() };

      // 출발지 마커 표시
      if (originMarker) originMarker.setMap(null);
      originMarker = new kakao.maps.Marker({
        map: map.value,
        position: latlng,
        title: '출발지',
      });
      removePick();  // 한 번 클릭하면 대기 해제
    };
    kakao.maps.event.addListener(map.value, 'click', pickClickListener);
  } else {
    removePick();
  }
}

function getCurrentPosition() {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) return reject(new Error('geolocation_unsupported'));
    navigator.geolocation.getCurrentPosition(
      pos => resolve({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      err => reject(err),
      { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 },
    );
  });
}

async function drawRoute() {
  if (!selectedBank.value || !map.value) return;
  routeLoading.value = true;
  routeError.value = '';
  // 이전 경로선·출발지 마커만 지우고, currentOrigin(pick 좌표)은 유지
  if (routePolyline.value) { routePolyline.value.setMap(null); routePolyline.value = null; }
  if (originMarker) { originMarker.setMap(null); originMarker = null; }
  routeInfo.value = null;
  try {
    // 1. 출발지 좌표 결정
    let origin;
    if (originMode.value === 'gps') {
      try {
        origin = await getCurrentPosition();
        currentOrigin.value = origin;
      } catch (geoErr) {
        routeError.value = geoErr.message === 'geolocation_unsupported'
          ? '이 브라우저는 위치 서비스를 지원하지 않습니다.'
          : '위치 권한을 허용해 주세요. (주소창 자물쇠 → 위치 허용)';
        return;
      }
    } else {
      if (!currentOrigin.value) {
        routeError.value = '지도에서 출발지를 먼저 클릭해 주세요.';
        return;
      }
      origin = currentOrigin.value;
    }

    // 2. 경로 API 호출
    const { data } = await api.get('/banks/route/', {
      params: {
        origin_lat: origin.lat,
        origin_lng: origin.lng,
        dest_lat: selectedBank.value.latitude,
        dest_lng: selectedBank.value.longitude,
      },
    });

    if (data.error && !data.vertices?.length) {
      routeError.value = data.error;
      return;
    }
    routeInfo.value = { distance: data.distance, duration: data.duration };

    // 3. 출발지 커스텀 오버레이 (파란 점)
    const originContent = `
      <div style="position:relative;width:22px;height:22px;display:flex;align-items:center;justify-content:center;">
        <div style="position:absolute;width:22px;height:22px;border-radius:50%;background:rgba(0,70,255,0.15);animation:pulse 1.8s infinite;"></div>
        <div style="width:14px;height:14px;border-radius:50%;background:#0046ff;border:2.5px solid white;box-shadow:0 2px 6px rgba(0,70,255,.5);"></div>
      </div>`;
    originMarker = new kakao.maps.CustomOverlay({
      map: map.value,
      position: new kakao.maps.LatLng(origin.lat, origin.lng),
      content: originContent,
      yAnchor: 0.5,
      xAnchor: 0.5,
    });

    // 4. 경로 Polyline 그리기
    const path = data.vertices.map(v => new kakao.maps.LatLng(v.lat, v.lng));
    const poly = new kakao.maps.Polyline({
      path,
      strokeWeight: 5,
      strokeColor: '#0046ff',
      strokeOpacity: 0.85,
      strokeStyle: 'solid',
    });
    poly.setMap(map.value);
    routePolyline.value = poly;

    // 5. 경로 전체 보이도록 지도 조정
    const bounds = new kakao.maps.LatLngBounds();
    path.forEach(p => bounds.extend(p));
    bounds.extend(new kakao.maps.LatLng(origin.lat, origin.lng));
    map.value.setBounds(bounds);
  } catch {
    routeError.value = '경로 조회 중 오류가 발생했습니다.';
  } finally {
    routeLoading.value = false;
  }
}

function clearRoute() {
  if (routePolyline.value) { routePolyline.value.setMap(null); routePolyline.value = null; }
  if (originMarker) { originMarker.setMap(null); originMarker = null; }
  removePick();
  routeInfo.value = null;
  routeError.value = '';
  currentOrigin.value = null;
}

// 💡 추가됨: 드롭다운을 위한 지역 데이터 세팅
const selectedSido = ref('');
const selectedSigungu = ref('');
const keyword = ref('');

// 전국 모든 시/군/구 데이터를 넣기엔 너무 기니까 대표적인 곳들만 샘플로 넣었습니다.
// 나중에 인터넷에서 '대한민국 행정구역 JSON'을 검색해서 이 객체만 교체해주시면 전국 서비스가 됩니다!
// 대한민국 전국 17개 시/도 및 250여 개 시/군/구 완벽 데이터
const regionData = {
  '서울': ['강남구', '강동구', '강북구', '강서구', '관악구', '광진구', '구로구', '금천구', '노원구', '도봉구', '동대문구', '동작구', '마포구', '서대문구', '서초구', '성동구', '성북구', '송파구', '양천구', '영등포구', '용산구', '은평구', '종로구', '중구', '중랑구'],
  '부산': ['강서구', '금정구', '기장군', '남구', '동구', '동래구', '부산진구', '북구', '사상구', '사하구', '서구', '수영구', '연제구', '영도구', '중구', '해운대구'],
  '대구': ['남구', '달서구', '달성군', '동구', '북구', '서구', '수성구', '중구', '군위군'],
  '인천': ['강화군', '계양구', '미추홀구', '남동구', '동구', '부평구', '서구', '연수구', '옹진군', '중구'],
  '광주': ['광산구', '남구', '동구', '북구', '서구'],
  '대전': ['대덕구', '동구', '서구', '유성구', '중구'],
  '울산': ['남구', '동구', '북구', '중구', '울주군'],
  '세종': ['세종특별자치시'],
  '경기': ['가평군', '고양시', '과천시', '광명시', '광주시', '구리시', '군포시', '김포시', '남양주시', '동두천시', '부천시', '성남시', '수원시', '시흥시', '안산시', '안성시', '안양시', '양주시', '양평군', '여주시', '연천군', '오산시', '용인시', '의왕시', '의정부시', '이천시', '파주시', '평택시', '포천시', '하남시', '화성시'],
  '강원': ['강릉시', '고성군', '동해시', '삼척시', '속초시', '양구군', '양양군', '영월군', '원주시', '인제군', '정선군', '철원군', '춘천시', '태백시', '평창군', '홍천군', '화천군', '횡성군'],
  '충북': ['괴산군', '단양군', '보은군', '영동군', '옥천군', '음성군', '제천시', '증평군', '진천군', '청주시', '충주시'],
  '충남': ['계룡시', '공주시', '금산군', '논산시', '당진시', '보령시', '부여군', '서산시', '서천군', '아산시', '예산군', '천안시', '청양군', '태안군', '홍성군'],
  '전북': ['고창군', '군산시', '김제시', '남원시', '무주군', '부안군', '순창군', '완주군', '익산시', '임실군', '장수군', '전주시', '정읍시', '진안군'],
  '전남': ['강진군', '고흥군', '곡성군', '광양시', '구례군', '나주시', '담양군', '목포시', '무안군', '보성군', '순천시', '신안군', '여수시', '영광군', '영암군', '완도군', '장성군', '장흥군', '진도군', '함평군', '해남군', '화순군'],
  '경북': ['경산시', '경주시', '고령군', '구미시', '김천시', '문경시', '봉화군', '상주시', '성주군', '안동시', '영덕군', '영양군', '영주시', '영천시', '예천군', '울릉군', '울진군', '의성군', '청도군', '청송군', '칠곡군', '포항시'],
  '경남': ['거제시', '거창군', '고성군', '김해시', '남해군', '밀양시', '사천시', '산청군', '양산시', '의령군', '진주시', '창녕군', '창원시', '통영시', '하동군', '함안군', '함양군', '합천군'],
  '제주': ['서귀포시', '제주시']
};

// 사용자가 '시/도'를 선택하면, 거기에 맞는 '시/군/구' 목록을 계산해주는 함수
const currentSigunguList = computed(() => {
  return selectedSido.value ? regionData[selectedSido.value] : [];
});

// 1. 카카오맵 스크립트 로드
function loadScript() {
  return new Promise((resolve, reject) => {
    if (window.kakao?.maps) return resolve();
    const s = document.createElement('script');
    s.src = `https://dapi.kakao.com/v2/maps/sdk.js?appkey=${import.meta.env.VITE_KAKAO_MAP_KEY}&autoload=false&libraries=services`;
    s.onload = resolve;
    s.onerror = reject;
    document.head.appendChild(s);
  });
}

// 2. 지도 초기화
function initMap(lat = 36.1194, lng = 128.3445) {
  if (!window.kakao?.maps) return;
  map.value = new kakao.maps.Map(document.getElementById('map'), { 
    center: new kakao.maps.LatLng(lat, lng), 
    level: 5 
  });

  kakao.maps.event.addListener(map.value, 'idle', () => {
    isMapMoved.value = true;
  });

  searchInCurrentArea();
}

function searchBanks() {
  if (!selectedSido.value || !selectedSigungu.value) {
    error.value = '시/도 와 시/군/구를 모두 선택해주세요.';
    return;
  }
  error.value = '';
  
  loading.value = true;
  const searchQuery = `${selectedSido.value} ${selectedSigungu.value} ${keyword.value || '은행'}`.trim();
  
  const ps = new kakao.maps.services.Places();

  ps.keywordSearch(searchQuery, (data, status) => {
    if (status === kakao.maps.services.Status.OK) {
      updatePlaces(data);
      
      // 검색된 결과가 다 보이도록 지도 카메라 이동
      const bounds = new kakao.maps.LatLngBounds();
      data.forEach(place => bounds.extend(new kakao.maps.LatLng(place.y, place.x)));
      map.value.setBounds(bounds);
      
      isMapMoved.value = false;
    } else if (status === kakao.maps.services.Status.ZERO_RESULT) {
      banks.value = [];
      error.value = '해당 지역에 검색된 은행이 없습니다.';
    } else {
      error.value = '검색 중 오류가 발생했습니다.';
    }
    loading.value = false;
  }, { category_group_code: 'BK9' }); // 은행 카테고리만 필터링
}

// 4. 지도 화면 내에서 재검색
function searchInCurrentArea() {
  loading.value = true;
  error.value = '';
  const ps = new kakao.maps.services.Places();

  ps.categorySearch('BK9', (data, status) => {
    if (status === kakao.maps.services.Status.OK) {
      updatePlaces(data);
      isMapMoved.value = false;
    } else if (status === kakao.maps.services.Status.ZERO_RESULT) {
      banks.value = [];
      error.value = '현재 화면 반경에 은행이 없습니다.';
      isMapMoved.value = false;
    }
    loading.value = false;
  }, { bounds: map.value.getBounds() });
}

// 현재 열린 InfoWindow
let openInfoWindow = null

// 5. 화면에 마커 렌더링
function updatePlaces(data) {
  banks.value = data.map(b => ({
    id: b.id,
    bank_name: b.place_name,
    address: b.road_address_name || b.address_name,
    phone: b.phone,
    place_url: b.place_url,
    latitude: b.y,
    longitude: b.x
  }));

  markers.forEach(m => m.setMap(null));
  markers.splice(0);
  if (openInfoWindow) { openInfoWindow.close(); openInfoWindow = null; }
  selectedBankId.value = null;
  selectedBank.value = null;
  originMode.value = 'gps';
  clearRoute();

  banks.value.forEach((b) => {
    const position = new kakao.maps.LatLng(b.latitude, b.longitude);
    const marker = new kakao.maps.Marker({
      map: map.value,
      position,
      title: b.bank_name
    });

    const infoWindow = new kakao.maps.InfoWindow({
      content: buildInfoContent(b),
      removable: true,
    });

    kakao.maps.event.addListener(marker, 'click', () => {
      if (openInfoWindow) openInfoWindow.close();
      infoWindow.open(map.value, marker);
      openInfoWindow = infoWindow;
      selectedBankId.value = b.id;
      selectedBank.value = b;
      clearRoute();
    });

    marker._infoWindow = infoWindow;
    marker._bank = b;
    markers.push(marker);
  });
}

function buildInfoContent(b) {
  return `
    <div style="padding:14px 16px;min-width:220px;font-family:inherit;line-height:1.5;">
      <strong style="font-size:1rem;color:#111;display:block;margin-bottom:6px;">${b.bank_name}</strong>
      <p style="margin:0 0 3px;font-size:.85rem;color:#555;">📍 ${b.address || '주소 없음'}</p>
      <p style="margin:0 0 8px;font-size:.85rem;color:#555;">📞 ${b.phone || '전화번호 없음'}</p>
      ${b.place_url ? `<a href="${b.place_url}" target="_blank" rel="noopener"
        style="display:inline-block;padding:5px 12px;background:#0046ff;color:white;
               border-radius:6px;font-size:.8rem;text-decoration:none;font-weight:600;">
        운영시간 · 상세정보 →
      </a>` : ''}
    </div>
  `;
}

function focusBank(bank) {
  const marker = markers.find(m => m._bank?.id === bank.id);
  if (!marker) return;
  map.value.setCenter(new kakao.maps.LatLng(bank.latitude, bank.longitude));
  map.value.setLevel(3);
  if (openInfoWindow) openInfoWindow.close();
  marker._infoWindow.open(map.value, marker);
  openInfoWindow = marker._infoWindow;
  selectedBankId.value = bank.id;
  selectedBank.value = bank;
  clearRoute();
}

function _drawMyLocation(lat, lng) {
  // 기존 내 위치 오버레이 제거
  if (myLocationOverlay) myLocationOverlay.setMap(null);

  const pos = new kakao.maps.LatLng(lat, lng);

  // 파란 점 커스텀 오버레이
  const content = `
    <div style="
      position:relative; width:22px; height:22px;
      display:flex; align-items:center; justify-content:center;
    ">
      <div style="
        position:absolute; width:22px; height:22px; border-radius:50%;
        background:rgba(0,70,255,0.15); animation:pulse 1.8s infinite;
      "></div>
      <div style="
        width:14px; height:14px; border-radius:50%;
        background:#0046ff; border:2.5px solid white;
        box-shadow:0 2px 6px rgba(0,70,255,.5);
      "></div>
    </div>
  `;

  myLocationOverlay = new kakao.maps.CustomOverlay({
    map: map.value,
    position: pos,
    content,
    yAnchor: 0.5,
    xAnchor: 0.5,
  });

  // 줌 레벨 4로 (걸어서 찾기 좋은 반경)
  map.value.setLevel(4);
  map.value.setCenter(pos);
}

function locate() {
  if (!navigator.geolocation) {
    error.value = '이 브라우저는 위치 서비스를 지원하지 않습니다.';
    return;
  }
  loading.value = true;
  error.value = '';

  navigator.geolocation.getCurrentPosition(
    (position) => {
      const lat = position.coords.latitude;
      const lng = position.coords.longitude;

      // 1. 내 위치 파란 점 마커 + 지도 이동
      _drawMyLocation(lat, lng);

      // 2. 지도 이동 완료(idle) 후 주변 은행 검색
      kakao.maps.event.addListenerOnce(map.value, 'idle', () => {
        // bounds-based 검색 → 실패 시 location-based fallback
        const ps = new kakao.maps.services.Places();
        const myLatLng = new kakao.maps.LatLng(lat, lng);

        ps.categorySearch('BK9', (data, status) => {
          if (status === kakao.maps.services.Status.OK) {
            updatePlaces(data);
          } else {
            // fallback: 반경 1.5km 검색
            ps.categorySearch('BK9', (data2, status2) => {
              if (status2 === kakao.maps.services.Status.OK) {
                updatePlaces(data2);
              } else {
                banks.value = [];
                error.value = '주변에 은행이 없습니다.';
              }
              loading.value = false;
            }, { location: myLatLng, radius: 1500 });
            return;
          }
          isMapMoved.value = false;
          loading.value = false;
        }, { bounds: map.value.getBounds() });
      });
    },
    (err) => {
      loading.value = false;
      if (err.code === 1) {
        error.value = '위치 권한을 허용해주세요. (주소창 왼쪽 자물쇠 아이콘 → 위치 허용)';
      } else if (err.code === 2) {
        error.value = '위치를 확인할 수 없습니다. 잠시 후 다시 시도해주세요.';
      } else {
        error.value = '위치 조회 시간이 초과되었습니다.';
      }
    },
    { enableHighAccuracy: true, timeout: 10000, maximumAge: 30000 }
  );
}

onMounted(async () => {
  try {
    await loadScript();
    kakao.maps.load(() => initMap());
  } catch {
    error.value = '지도를 불러오지 못했습니다.';
  }
});
</script>

<style scoped>
.layout { display: grid; grid-template-columns: 380px 1fr; height: calc(100dvh - 80px); max-height: calc(100dvh - 80px); overflow: hidden; }
aside { min-height: 0; display: flex; flex-direction: column; padding: 24px; overflow: hidden; background: #f8f9fa; box-sizing: border-box; }
h1 { font-size: 1.5rem; margin-bottom: 20px; }

/* 💡 추가된 드롭다운 스타일 */
.region-select-group { display: flex; gap: 8px; margin-bottom: 12px; }
.region-select-group select { flex: 1; padding: 10px; border: 1px solid #ddd; border-radius: 8px; font-size: 0.95rem; background: white; outline: none; cursor: pointer; }
.region-select-group select:disabled { background: #f1f3f5; cursor: not-allowed; }

.search-box { display: flex; gap: 8px; margin-bottom: 12px; }
.search-box input { flex: 1; padding: 12px; border: 1px solid #ddd; border-radius: 8px; font-size: 0.95rem; }
.search-btn { padding: 0 16px; background: #333; color: white; border: none; border-radius: 8px; cursor: pointer; font-weight: bold; }

.locate-btn { padding: 12px; background: #e8f0fe; color: #0046ff; border: 1px solid #0046ff; border-radius: 8px; font-weight: bold; cursor: pointer; margin-bottom: 15px; }
.status-msg { margin: 10px 0; font-weight: 500; }
.error { color: #c62828; }

.bank-results { min-height: 0; flex: 1; display: flex; flex-direction: column; overflow: hidden; border: 1px solid #e3e7ed; border-radius: 14px; background: white; box-shadow: 0 4px 14px rgba(31, 45, 72, .05); }
.results-header { flex: 0 0 auto; display: flex; align-items: center; justify-content: space-between; padding: 15px 16px; border-bottom: 1px solid #edf0f4; background: #fff; }
.results-header strong { font-size: .95rem; }
.results-header span { padding: 4px 8px; border-radius: 12px; background: #edf3ff; color: #0046ff; font-size: .75rem; font-weight: 700; }
.bank-list { min-height: 0; flex: 1; overflow-y: auto; padding: 10px; overscroll-behavior: contain; scrollbar-width: thin; scrollbar-color: #cbd3df transparent; }
.bank-list::-webkit-scrollbar { width: 6px; }
.bank-list::-webkit-scrollbar-thumb { border-radius: 6px; background: #cbd3df; }
.bank-list article { padding: 15px; margin-bottom: 9px; background: #f8f9fb; border-radius: 10px; border: 1px solid transparent; transition: border-color .18s ease, background-color .18s ease; }
.bank-list article:hover { border-color: #cddaff; background: #f3f6ff; }
.bank-list article.selected { border-color: #0046ff; background: #eef3ff; }
.bank-list article:last-of-type { margin-bottom: 0; }
.bank-list b { color: #111; font-size: 1.1rem; display: block; margin-bottom: 6px; }
.bank-list p { color: #555; font-size: 0.9rem; margin-bottom: 4px; }
.bank-list small { color: #888; }
.empty-result { padding: 28px 12px; color: #8a93a2 !important; text-align: center; line-height: 1.6; }

.map-wrap { position: relative; width: 100%; height: 100%; }
#map { width: 100%; height: 100%; }

@keyframes pulse {
  0% { transform: scale(1); opacity: .6; }
  70% { transform: scale(2.2); opacity: 0; }
  100% { transform: scale(1); opacity: 0; }
}

.research-btn {
  position: absolute; top: 20px; left: 50%; transform: translateX(-50%); z-index: 10;
  padding: 10px 20px; background: white; color: #0046ff; border: 1px solid #0046ff;
  border-radius: 20px; font-weight: bold; box-shadow: 0 4px 6px rgba(0,0,0,0.1); cursor: pointer;
}

/* 경로 사이드바 */
.route-sidebar { display: flex; flex-direction: column; gap: 12px; flex: 1; min-height: 0; overflow-y: auto; }

.back-to-list {
  display: inline-flex; align-items: center; gap: 4px;
  padding: 7px 12px; border: 1px solid #e7eaf0; border-radius: 8px;
  background: white; color: #616b7d; font-size: .82rem; font-weight: 600; cursor: pointer;
  align-self: flex-start;
}
.back-to-list:hover { border-color: #0046ff; color: #0046ff; }

.dest-bank-card {
  background: #f7f8fb; border: 1px solid #e7eaf0; border-radius: 12px; padding: 12px 14px;
}
.dest-bank-card strong { display: block; font-size: .95rem; color: #191f2b; margin-bottom: 4px; }
.dest-bank-card p { margin: 0 0 2px; font-size: .8rem; color: #616b7d; }
.dest-bank-card small { color: #98a2b3; font-size: .75rem; }

.route-divider { height: 1px; background: #f0f2f6; }
.route-label { margin: 0; font-size: .78rem; font-weight: 700; color: #364153; }

/* 출발지 모드 탭 */
.origin-mode-tabs { display: flex; gap: 6px; }
.origin-tab {
  flex: 1; padding: 8px 0; border: 1px solid #e7eaf0; border-radius: 10px;
  background: white; color: #616b7d; font-size: .8rem; font-weight: 600; cursor: pointer;
  transition: all .15s;
}
.origin-tab:hover { border-color: #0046ff; color: #0046ff; }
.origin-tab.active { background: #0046ff; border-color: #0046ff; color: white; }
.origin-tab.picking { background: #fff8e6; border-color: #f5a623; color: #c68400; animation: blink .9s step-start infinite; }
@keyframes blink { 50% { opacity: .5; } }

.pick-hint { margin: 0; font-size: .78rem; color: #c68400; font-weight: 600; }
.pick-confirmed { margin: 0; font-size: .78rem; color: #00a984; font-weight: 600; }

/* 경로 흐름 */
.route-flow { display: flex; flex-direction: column; gap: 0; background: #f7f8fb; border-radius: 12px; padding: 12px 14px; }
.flow-row { display: flex; align-items: center; gap: 10px; }
.flow-dot { width: 12px; height: 12px; border-radius: 50%; flex: 0 0 auto; }
.origin-dot { background: #0046ff; }
.dest-dot { background: #e53e3e; }
.flow-label { font-size: .83rem; font-weight: 600; color: #191f2b; }
.flow-line {
  margin-left: 5px; border-left: 2px dashed #d0d5dd;
  padding: 6px 0 6px 18px; min-height: 28px;
  display: flex; align-items: center;
}
.flow-meta { font-size: .78rem; font-weight: 700; color: #0046ff; }

.route-error { margin: 0; font-size: .78rem; color: #e53e3e; font-weight: 600; }

.route-go-btn {
  padding: 12px 0; background: #0046ff; color: white; border: none; border-radius: 12px;
  font-size: .9rem; font-weight: 700; cursor: pointer; transition: background .15s;
}
.route-go-btn:hover:not(:disabled) { background: #0036cc; }
.route-go-btn:disabled { background: #a0bbf2; cursor: not-allowed; }
.route-clear-btn {
  padding: 9px 0; background: #f0f2f7; color: #364153; border: none; border-radius: 12px;
  font-size: .84rem; font-weight: 600; cursor: pointer;
}
.route-clear-btn:hover { background: #e0e3ec; }

@media(max-width:750px) {
  .layout { height: calc(100dvh - 80px); max-height: calc(100dvh - 80px); display: flex; flex-direction: column-reverse; }
  aside { min-height: 0; flex: 1 1 58%; padding: 16px; }
  aside h1 { margin: 0 0 12px; font-size: 1.25rem; }
  .map-wrap { flex: 0 0 42%; height: auto; }
  .locate-btn { margin-bottom: 10px; }
}
</style>
