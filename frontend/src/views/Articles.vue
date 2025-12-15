<template>
  <Layout>
    <div class="articles-page">
      <!-- 统计卡片 -->
      <div class="stats-cards">
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon total">
              <el-icon><Document /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ totalArticles }}</div>
              <div class="stat-label">总文章数</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon today">
              <el-icon><Calendar /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ todayCount }}</div>
              <div class="stat-label">今日文章</div>
            </div>
          </div>
        </el-card>
        <el-card class="stat-card">
          <div class="stat-content">
            <div class="stat-icon category">
              <el-icon><Collection /></el-icon>
            </div>
            <div class="stat-info">
              <div class="stat-value">{{ categories.length }}</div>
              <div class="stat-label">分类数量</div>
            </div>
          </div>
        </el-card>
      </div>

      <!-- 筛选栏 -->
      <el-card class="filter-card">
        <div class="filter-header">
          <div class="filter-title">
            <el-icon><Filter /></el-icon>
            <span>筛选条件</span>
          </div>
          <el-button size="small" type="primary" :icon="Refresh" @click="fetchArticles" :loading="loading.articles">
            刷新
          </el-button>
        </div>
        <div class="filter-content">
          <div class="filter-row">
            <div class="filter-item">
              <label>搜索标题</label>
              <el-input
                v-model="articleQuery"
                size="default"
                placeholder="输入关键词搜索..."
                clearable
                @keydown.enter="fetchArticles"
                @clear="fetchArticles"
              >
                <template #prefix>
                  <el-icon><Search /></el-icon>
                </template>
              </el-input>
            </div>
            <div class="filter-item">
              <label>公众号筛选</label>
              <el-select
                v-model="selectedMpName"
                size="default"
                placeholder="全部公众号"
                clearable
                filterable
                @change="fetchArticles"
                style="width: 180px"
              >
                <el-option label="全部" value="" />
                <el-option v-for="mp in mpNames" :key="mp" :label="mp" :value="mp" />
              </el-select>
            </div>
            <div class="filter-item">
              <label>分类筛选</label>
              <el-select
                v-model="selectedCategory"
                size="default"
                placeholder="全部分类"
                clearable
                @change="fetchArticles"
                style="width: 180px"
              >
                <el-option label="全部" value="" />
                <el-option v-for="cat in categories" :key="cat" :label="cat" :value="cat" />
              </el-select>
            </div>
            <div class="filter-item">
              <label>时间范围</label>
              <el-switch
                v-model="todayOnly"
                active-text="仅今日"
                inactive-text="全部"
                @change="fetchArticles"
              />
            </div>
            <div class="filter-item">
              <label>排序方式</label>
              <el-select v-model="articleSort" size="default" style="width: 140px" @change="fetchArticles">
                <el-option label="时间倒序" value="desc" />
                <el-option label="时间正序" value="asc" />
              </el-select>
            </div>
            <div class="filter-item">
              <label>视图模式</label>
              <el-radio-group v-model="articleView" size="default" @change="onArticleViewChange">
                <el-radio-button label="table">
                  <el-icon><List /></el-icon>
                  <span>列表</span>
                </el-radio-button>
                <el-radio-button label="card">
                  <el-icon><Grid /></el-icon>
                  <span>图标</span>
                </el-radio-button>
                <el-radio-button label="mp">
                  <el-icon><DataAnalysis /></el-icon>
                  <span>汇总</span>
                </el-radio-button>
              </el-radio-group>
            </div>
          </div>
        </div>
      </el-card>

      <!-- 文章列表 -->
      <el-card class="content-card">
        <!-- 列表视图（表格） -->
            <template v-if="articleView === 'table'">
              <div v-if="articles.length === 0" class="empty-state">
                <el-icon class="empty-icon"><DocumentDelete /></el-icon>
                <p>暂无文章数据</p>
              </div>
              <el-table v-else :data="articles" style="width: 100%" size="default" stripe border>
            <el-table-column fixed type="index" label="序号" width="60" />
            <el-table-column prop="mp_name" label="公众号" width="180">
              <template #default="scope">
                <div class="table-mp-cell">
                  <img
                    v-if="scope.row.mp_avatar"
                    :src="scope.row.mp_avatar"
                    class="mp-avatar-img"
                    @error="handleAvatarError"
                  />
                  <el-icon v-else class="mp-avatar-icon"><User /></el-icon>
                  <el-tooltip :content="scope.row.mp_name || '未知'" placement="top" :disabled="!scope.row.mp_name || scope.row.mp_name.length <= 10">
                    <span class="mp-name-text">{{ scope.row.mp_name || "未知" }}</span>
                  </el-tooltip>
                </div>
              </template>
            </el-table-column>
            <el-table-column prop="category" label="分类" width="120">
              <template #default="scope">
                <el-tag v-if="scope.row.category" size="small" type="info">{{ scope.row.category }}</el-tag>
                <span v-else class="text-muted">-</span>
              </template>
            </el-table-column>
            <el-table-column prop="title" label="标题" min-width="300" show-overflow-tooltip />
            <el-table-column label="发布时间" width="180">
              <template #default="scope">{{ formatTime(scope.row.publish_at) }}</template>
            </el-table-column>
            <el-table-column label="操作" width="120" fixed="right">
              <template #default="scope">
                <el-button size="small" type="primary" link @click="openArticle(scope.row.url)">
                  <el-icon><Link /></el-icon>
                  打开
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <div class="pager-wrapper">
            <el-pagination
              background
              layout="total, sizes, prev, pager, next, jumper"
              :page-size="articlesPageSize"
              :page-sizes="[20, 50, 100]"
              :total="totalArticles"
              :current-page="articlesPage"
              @size-change="handleArticleSizeChange"
              @current-change="handleArticleCurrentChange"
            />
          </div>
        </template>

        <!-- 图标视图（卡片） -->
        <template v-else-if="articleView === 'card'">
          <div v-if="articles.length === 0" class="empty-state">
            <el-icon class="empty-icon"><DocumentDelete /></el-icon>
            <p>暂无文章数据</p>
          </div>
          <div v-else class="articles-grid">
            <div
              v-for="article in articles"
              :key="article.id"
              class="article-card"
              @click="openArticle(article.url)"
            >
              <div class="article-header">
                <div class="article-mp">
                  <img
                    v-if="article.mp_avatar"
                    :src="article.mp_avatar"
                    class="article-mp-avatar"
                    @error="handleAvatarError"
                  />
                  <el-icon v-else class="article-mp-icon"><User /></el-icon>
                  <el-tooltip :content="article.mp_name || '未知'" placement="top" :disabled="!article.mp_name || article.mp_name.length <= 10">
                    <span class="mp-name-text">{{ article.mp_name || "未知" }}</span>
                  </el-tooltip>
                </div>
                <div class="article-time">
                  <el-icon><Clock /></el-icon>
                  <span>{{ formatTime(article.publish_at) }}</span>
                </div>
              </div>
              <div v-if="article.category" class="article-category">
                <el-tag size="small" type="info">{{ article.category }}</el-tag>
              </div>
              <div class="article-title">{{ article.title }}</div>
              <div class="article-footer">
                <el-button size="small" type="primary" link @click.stop="openArticle(article.url)">
                  <el-icon><Link /></el-icon>
                  阅读全文
                </el-button>
              </div>
            </div>
          </div>
          <div class="pager-wrapper">
            <el-pagination
              background
              layout="total, sizes, prev, pager, next, jumper"
              :page-size="articlesPageSize"
              :page-sizes="[20, 50, 100]"
              :total="totalArticles"
              :current-page="articlesPage"
              @size-change="handleArticleSizeChange"
              @current-change="handleArticleCurrentChange"
            />
          </div>
        </template>

        <!-- 公众号汇总视图 -->
        <template v-else>
          <div class="mp-summary-grid">
            <el-card
              v-for="mp in mpSummary"
              :key="mp.mp_name"
              class="mp-card"
              shadow="hover"
              @click="viewMpArticles(mp.mp_name)"
            >
              <div class="mp-card-content">
                <div class="mp-avatar">
                  <img
                    v-if="mp.mp_avatar"
                    :src="mp.mp_avatar"
                    class="mp-avatar-img-large"
                    @error="handleAvatarError"
                  />
                  <el-icon v-else><UserFilled /></el-icon>
                </div>
                <div class="mp-info">
                  <el-tooltip :content="mp.mp_name" placement="top" :disabled="!mp.mp_name || mp.mp_name.length <= 12">
                    <div class="mp-name">{{ mp.mp_name }}</div>
                  </el-tooltip>
                  <div class="mp-stats">
                    <span class="mp-count">{{ mp.count }} 篇文章</span>
                    <span class="mp-time">最新：{{ formatTime(mp.latest) }}</span>
                  </div>
                </div>
              </div>
            </el-card>
          </div>
        </template>
      </el-card>
    </div>
  </Layout>
</template>

<script setup>
import { ref, computed, onMounted } from "vue";
import dayjs from "dayjs";
import http from "../api/http";
import { ElMessage } from "element-plus";
import {
  Document,
  Calendar,
  Collection,
  Filter,
  Refresh,
  Search,
  List,
  Grid,
  DataAnalysis,
  DocumentDelete,
  User,
  Clock,
  Link,
  UserFilled,
} from "@element-plus/icons-vue";
import Layout from "./Layout.vue";

const articles = ref([]);
const totalArticles = ref(0); // 总文章数（从后端获取）
const categories = ref([]);
const mpNames = ref([]);
const loading = ref({ articles: false, mpSummary: false });
const mpSummaryData = ref([]); // 从后端获取的公众号汇总数据
const articleQuery = ref("");
const selectedCategory = ref("");
const selectedMpName = ref("");
const todayOnly = ref(false);
const articleView = ref("table"); // 默认列表视图
const articleSort = ref("desc");
const articlesPage = ref(1);
const articlesPageSize = ref(20);

const formatTime = (val) => (val ? dayjs(val).format("YYYY-MM-DD HH:mm") : "");

const fetchCategories = async () => {
  try {
    const { data } = await http.get("/targets/categories");
    categories.value = data || [];
  } catch {
    // 忽略错误，分类是可选的
  }
};

const fetchMpNames = async () => {
  try {
    const { data } = await http.get("/articles/mp-names");
    mpNames.value = data || [];
  } catch {
    // 忽略错误，公众号列表是可选的
  }
};

const fetchArticles = async () => {
  loading.value.articles = true;
  try {
    const params = {
      page: articlesPage.value,
      page_size: articlesPageSize.value,
      q: articleQuery.value,
    };
    if (selectedCategory.value) {
      params.category = selectedCategory.value;
    }
    if (selectedMpName.value) {
      params.mp_name = selectedMpName.value;
    }
    if (todayOnly.value) {
      const start = dayjs().startOf("day").toISOString();
      const end = dayjs().endOf("day").toISOString();
      params.start = start;
      params.end = end;
    }
    const { data } = await http.get("/articles", { params });
    articles.value = data.items || [];
    totalArticles.value = data.total || 0;
  } catch {
    ElMessage.error("获取文章失败");
  } finally {
    loading.value.articles = false;
  }
};

const todayCount = computed(() => {
  // 今日文章数需要单独查询，这里暂时使用当前页的数据估算
  // 如果需要精确值，可以添加一个单独的API
  const today = dayjs().startOf("day");
  return articles.value.filter((article) => {
    const publishTime = dayjs(article.publish_at);
    return publishTime.isSame(today, "day");
  }).length;
});

const fetchMpSummary = async () => {
  loading.value.mpSummary = true;
  try {
    const { data } = await http.get("/articles/mp-summary");
    mpSummaryData.value = data || [];
  } catch {
    ElMessage.error("获取公众号汇总失败");
  } finally {
    loading.value.mpSummary = false;
  }
};

const mpSummary = computed(() => {
  // 使用从后端获取的完整汇总数据
  if (articleView.value === "icon" && mpSummaryData.value.length > 0) {
    return mpSummaryData.value.map((item) => ({
      mp_name: item.mp_name,
      count: item.count,
      latest: item.latest_publish_at ? new Date(item.latest_publish_at).getTime() : 0,
      mp_avatar: item.mp_avatar,
    }));
  }
  // 如果还没有加载汇总数据，回退到使用当前页数据（兼容）
  const map = new Map();
  articles.value.forEach((item) => {
    const key = item.mp_name || "未知";
    const ts = new Date(item.publish_at || item.created_at || 0).getTime();
    if (!map.has(key)) {
      map.set(key, { mp_name: key, count: 0, latest: 0, mp_avatar: item.mp_avatar });
    }
    const obj = map.get(key);
    obj.count += 1;
    obj.latest = Math.max(obj.latest, ts);
  });
  return Array.from(map.values()).sort((a, b) => b.count - a.count);
});

const onArticleViewChange = () => {
  // 切换到汇总视图时，加载完整的汇总数据
  if (articleView.value === "icon") {
    fetchMpSummary();
  }
};

const viewMpArticles = (mpName) => {
  // 切换到列表视图
  articleView.value = "table";
  // 设置公众号筛选
  selectedMpName.value = mpName;
  // 刷新文章列表
  fetchArticles();
};

const openArticle = (url) => {
  if (url) {
    window.open(url, "_blank");
  }
};

const handleAvatarError = (event) => {
  // 头像加载失败时隐藏图片
  event.target.style.display = "none";
};

const handleArticleSizeChange = (val) => {
  articlesPageSize.value = val;
  articlesPage.value = 1;
  fetchArticles(); // 重新获取数据
};

const handleArticleCurrentChange = (val) => {
  articlesPage.value = val;
  fetchArticles(); // 重新获取数据
};

onMounted(() => {
  fetchCategories();
  fetchMpNames();
  fetchArticles();
  // 如果默认是汇总视图，加载汇总数据
  if (articleView.value === "icon") {
    fetchMpSummary();
  }
});
</script>

<style scoped>
.articles-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

/* 统计卡片 */
.stats-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 8px;
}

.stat-card {
  border-radius: 12px;
  transition: all 0.3s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.12);
}

.stat-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.stat-icon {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 24px;
  color: #fff;
}

.stat-icon.total {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.stat-icon.today {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.stat-icon.category {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.stat-info {
  flex: 1;
}

.stat-value {
  font-size: 28px;
  font-weight: 700;
  color: #1f2d3d;
  line-height: 1.2;
}

.stat-label {
  font-size: 14px;
  color: #909399;
  margin-top: 4px;
}

/* 筛选卡片 */
.filter-card {
  border-radius: 12px;
}

.filter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #ebeef5;
}

.filter-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 600;
  font-size: 16px;
  color: #1f2d3d;
}

.filter-content {
  padding: 8px 0;
}

.filter-row {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  align-items: flex-end;
}

.filter-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
  min-width: 160px;
}

.filter-item label {
  font-size: 13px;
  color: #606266;
  font-weight: 500;
}

/* 内容卡片 */
.content-card {
  border-radius: 12px;
  min-height: 400px;
}

/* 空状态 */
.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80px 20px;
  color: #909399;
}

.empty-icon {
  font-size: 64px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  font-size: 16px;
  margin: 0;
}

/* 表格样式 */
.table-mp-cell {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0; /* 允许flex子元素收缩 */
  width: 100%;
}

.table-mp-cell .mp-name-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  vertical-align: middle;
}

.mp-avatar-img {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  object-fit: cover;
}

.mp-avatar-icon {
  width: 32px;
  height: 32px;
  color: #909399;
}

.text-muted {
  color: #909399;
}

/* 文章网格 */
.articles-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 20px;
  padding: 8px 0;
}

.article-card {
  background: #fff;
  border: 1px solid #ebeef5;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.3s ease;
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.article-card:hover {
  border-color: #409eff;
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.15);
  transform: translateY(-2px);
}

.article-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  font-size: 13px;
  color: #909399;
}

.article-mp {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0; /* 允许flex子元素收缩 */
}

.article-mp .mp-name-text {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.article-mp-avatar {
  width: 24px;
  height: 24px;
  border-radius: 50%;
  object-fit: cover;
}

.article-mp-icon {
  font-size: 18px;
}

.article-time {
  display: flex;
  align-items: center;
  gap: 6px;
}

.article-category {
  margin-top: -4px;
}

.article-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
  line-height: 1.5;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
  flex: 1;
}

.article-footer {
  display: flex;
  justify-content: flex-end;
  padding-top: 8px;
  border-top: 1px solid #f5f7fa;
}

/* 公众号汇总网格 */
.mp-summary-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 16px;
  padding: 8px 0;
}

.mp-card {
  border-radius: 12px;
  transition: all 0.3s ease;
  cursor: pointer;
}

.mp-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 20px rgba(64, 158, 255, 0.15);
}

.mp-card-content {
  display: flex;
  align-items: center;
  gap: 16px;
}

.mp-avatar {
  width: 56px;
  height: 56px;
  border-radius: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 24px;
  flex-shrink: 0;
  overflow: hidden;
}

.mp-avatar-img-large {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.mp-info {
  flex: 1;
  min-width: 0;
}

.mp-name {
  font-size: 16px;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 8px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.mp-stats {
  display: flex;
  flex-direction: column;
  gap: 4px;
  font-size: 13px;
  color: #909399;
}

.mp-count {
  font-weight: 500;
  color: #409eff;
}

/* 分页 */
.pager-wrapper {
  display: flex;
  justify-content: center;
  margin-top: 32px;
  padding-top: 24px;
  border-top: 1px solid #ebeef5;
}

/* 响应式 */
@media (max-width: 768px) {
  .stats-cards {
    grid-template-columns: 1fr;
  }

  .articles-grid {
    grid-template-columns: 1fr;
  }

  .filter-row {
    flex-direction: column;
  }

  .filter-item {
    width: 100%;
  }
}
</style>
