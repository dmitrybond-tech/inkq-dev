export type Lang = 'en' | 'ru';

export type CommonTranslations = {
  appName: string;
  signIn: string;
  signUp: string;
  signOut: string;
  dashboard: string;
  themeLight: string;
  themeDark: string;
};

export type LandingTranslations = {
  heroTitle: string;
  heroSubtitle: string;
  ctaFindArtist: string;
  ctaJoinAsArtist: string;
};

export type HeaderTranslations = {
  navArtists: string;
  navStudios: string;
  navModels: string;
};

export type ProfileTranslations = {
  aboutTitle: string;
  portfolioTitle: string;
  contactTitle: string;
  roleArtist: string;
  roleStudio: string;
  roleModel: string;
  aboutLabel: string;
  stylesLabel: string;
  cityLabel: string;
  studioLabel: string;
  sessionPriceLabel: string;
  instagramLabel: string;
  telegramLabel: string;
  profileTab: string;
  portfolioTab: string;
  wannadoTab: string;
  emptyAbout: string;
  emptyPortfolio: string;
  emptyWannado: string;
  studioNotFound: string;
  modelNotFound: string;
  errorLoadingStudio: string;
  errorLoadingModel: string;
  studiosTitle: string;
  worksAt: string;
  teamTitle: string;
};

export type AuthTranslations = {
  emailLabel: string;
  passwordLabel: string;
  accountTypeLabel: string;
  accountTypeArtist: string;
  accountTypeStudio: string;
  accountTypeModel: string;
  submitButton: string;
};

export type DashboardTranslations = {
  welcome: string;
  welcomeArtist: string;
  welcomeStudio: string;
  welcomeModel: string;
  navOverview: string;
  navProfile: string;
  navCalendar: string;
  navSettings: string;
};

export type OnboardingTranslations = {
  title: string;
  stepCompleteProfile: string;
  stepAddPortfolio: string;
  stepSetAvailability: string;
  stepAboutMeta: string;
  stepAvatarBanner: string;
  stepPortfolio: string;
  stepWannado: string;
  finishOnboarding: string;
  portfolioHint: string;
  wannadoHint: string;
};

export type CatalogTranslations = {
  title: string;
  noResults: string;
  subtitle: string;
  filterCity: string;
  filterStyle: string;
  allCities: string;
  anyStyle: string;
  stylesSelected: string;
  clearFilters: string;
  loadMore: string;
  errorLoading: string;
  retry: string;
  emptyWithFilters: string;
  resultsLabel: string;
};

export type CatalogStudiosTranslations = {
  title: string;
  subtitle: string;
  resultsLabel: string;
  empty: string;
  loadError: string;
};

export type CatalogModelsTranslations = {
  title: string;
  subtitle: string;
  resultsLabel: string;
  empty: string;
  loadError: string;
};

export type MediaTranslations = {
  avatarUpload: string;
  bannerUpload: string;
  portfolioUpload: string;
  selectFile: string;
  upload: string;
  uploading: string;
  uploadSuccess: string;
  uploadError: string;
  fileTooLarge: string;
  invalidFileType: string;
  delete: string;
  deleteConfirm: string;
  dragDrop: string;
  or: string;
  maxSize: string;
  supportedFormats: string;
  remove: string;
  addImages: string;
  noImages: string;
  imageEdit: string;
  imageSave: string;
  imageCancel: string;
  imageTitleLabel: string;
  imageDescriptionLabel: string;
  imageApproxPriceLabel: string;
  imageApproxPricePlaceholder: string;
  imagePlacementLabel: string;
};

export type I18nSchema = {
  common: CommonTranslations;
  landing: LandingTranslations;
  header: HeaderTranslations;
  profile: ProfileTranslations;
  auth: AuthTranslations;
  dashboard: DashboardTranslations;
  onboarding: OnboardingTranslations;
  catalog: CatalogTranslations;
  media: MediaTranslations;
  catalogStudios: CatalogStudiosTranslations;
  catalogModels: CatalogModelsTranslations;
};

