# VCPS Faz 0–5: Üç Turlu Derin İnceleme ve Güncellenmiş Plan

Tarih: 2026-10-07  
Kapsam: `standard/gates/`, `standard/VCPS.md`, `standard/versioning.md`,
`workflows/`, `templates/`, `adapters/install.py`, iki adaptörün kurulum ve
kabiliyet belgeleri, `evaluation/completion-roadmap.md`, değerlendirme ve
güvenlik kayıtları.  
Bu belge, Faz 0–5 için önerilen işi ve kanıta dayalı çıkış koşullarını
tanımlar; bu fazların uygulandığı veya kapıların geçtiği iddiası değildir.

## 1. Mevcut durumdan doğrulanabilenler

- Core, Gate 1–6'yı ve değişiklik risk sınıfına göre uygulanabilirlik
  matrisini tanımlıyor. Gate 6, değişiklik başına değil sürüm birimi başına
  ve olumlu insan kararıyla değerlendiriliyor.
- `templates/validation.md` 14 grup yapısal ve çapraz-kayıt kontrolünü
  tarif ediyor. Roadmap, `vcps_tool.py validate` uygulamasının bu
  kontrollerin bir kısmını tam, bir kısmını kısmi kapsadığını; tam bir Core
  uygunluk doğrulayıcısının henüz olmadığını söylüyor.
- `adapters/install.py` Claude Code için kopya/symlink, Codex için kopya,
  Codex kullanıcı-geneli kurulum ve Claude Core kopyalama akışları sağlıyor.
  Var olan hedef yolları ezmiyor ve kopyalanan dosyaları karşılaştırıyor.
- Codex becerileri kurulum sırasında Claude yardımcı dosyalarını hedefe
  taşıyor; bu belgelenmiş bir geçici bağımlılık. Adaptör bağımsızlığı henüz
  tam değil.
- Kurulum testi, geçici hedeflerde kurulum ve dosya eşitliğini doğrulayan
  yapısal/simüle edilmiş kontroller içeriyor. Kurulum arızasında tüm yazılmış
  dosyaları atomik olarak geri alan bir işlem modeli mevcut kodda görünmüyor.
- README ve katkı kılavuzu tek üst-seviye test komutu/CI olmadığını
  belirtiyor. Phase J kaydı, bir L3/R3 örneğinde gerekli CI kanıtı yokluğu
  nedeniyle Gate 4 ve Gate 5'in `BLOCKED` kaldığını gösteriyor.
- Claude tarafında SETUP, FEATURE ve REVIEW için belirli canlı kanıtlar var;
  diğer iş akışları için canlı kabul kanıtı eksik. Codex'te sınırlı salt-okunur
  fixture ve handoff kanıtı var, tam beceri/iş akışı kabulü yok. Sentetik
  projede gerçek bir sahip adına insan checkpoint'i veya kabul kararı
  üretilemez.
- Gate dokümanları bozulma sonrası yeniden kurulmuş. Recovery notları
  belirsizliği açıklıyor; özellikle Gate uygulanabilirlik matrisinin ve
  Gate 5'in bazı maddelerinin tarihsel kaynak güveni sınırlı.

## 2. İnceleme turu 1 — Ürün ve normatif kapılar

### İncelenen soru

Her fazda kimin hangi ihtiyacının karşılandığı, hangi kapıların gerekli
olduğu ve bir fazın tamamlandığının neyle kanıtlanacağı açık mı?

### Eklenmesi gereken işler

1. **Kullanıcı ve kullanım bağlamı profilleri:** Bağımsız geliştirici,
   mevcut projeye sonradan uyarlayan ekip, kurumsal/çok-bileşenli proje ve
   yalnızca bir adaptör kuran kullanıcı için başlangıç ve başarı ölçütleri
   tanımlansın. Kurulum kolaylığı yalnızca dosyaları kopyalamak değil,
   kullanıcıyı doğru Core/adaptör sürümüne ve güvenli çalıştırma ayarına
   götürmek olarak ele alınsın.
2. **Faz kapsam kartları:** Her faz için amaç, kapsam dışı kalan işler,
   bağımlılıklar, R sınıfı, uygulanacak Gate 1–5, beklenen kanıt sınıfı,
   insan checkpoint'i, kabul ölçütü ve sorumlu artefakt listelensin.
3. **Kapı-proje izi:** Gate gereklilikleri → workflow adımı → şema alanı →
   mekanik kontrol → senaryo → canlı kanıt zinciri çıkarılsın. Her
   gerekliliğin `COVERED`, `PARTIAL`, `NOT_COVERED`, `NOT_APPLICABLE`
   durumlarından biri ve gerekçesi olsun. Bu, “testler yeşil” bilgisinin
   Core uygunluğuyla karıştırılmasını engeller.
4. **Recovery metinlerinin bağımsız gözden geçirilmesi:** Gate matrisinin
   çıkarımsal hücreleri ve Gate 5'te yeni tasarım kararı olarak eklenen
   maddeler, özgün kaynak bulunursa onunla karşılaştırılsın; kaynak yoksa
   belirsizlik, Core değişikliği ve sürümleme gereksinimi açıkça kaydedilsin.
   Bu kontrol tamamlanana kadar tartışmalı matris hücrelerine dayanan
   otomatik `NOT_APPLICABLE`/`PASS` üretimi yapılmasın.
5. **Risk sınıfı ve bağımsızlık karar izi:** Her değerlendirme senaryosu
   değişiklik sınıfını, proje seviyesini, bağımsızlık modunu ve gerekli
   kanıt sadakatini belirtmeli. Özellikle `R0` hafif kapsam ile `R1` koşullu
   Gate 2/Gate 5 davranışı test matrisinde ayrı örneklenmeli.
6. **Kabul ile yayın kararını ayırma:** Ürün kabulü (Gate 1 / HC-14),
   değişiklik doğrulaması (Gate 4), güvenlik değerlendirmesi (Gate 5) ve
   sürüm onayı (Gate 6 / HC-10) doküman, kullanıcı arayüzü ve örneklerde
   ayrı durumlar olarak gösterilsin.

### Fazlara etkisi

Yukarıdaki işler yeni **Faz 0**'ın ana çıktılarıdır. Faz 2'deki doğrulayıcı
ve Faz 3–4 adaptör kabulü, bu gereklilik izini kapsama kanıtı olarak
kullanmalıdır. Kapıların kendisi gözden geçirilmeden uygulama kapıları
üzerinde otomasyon güvenilir sayılmamalıdır.

## 3. İnceleme turu 2 — Kurulum, güncelleme ve kurtarma deneyimi

### İncelenen soru

Yeni kullanıcı güvenli ve doğru kurulumu tek bir akışta yapabiliyor mu;
kurulum tekrarı, kısmi hata, yükseltme ve kaldırma anlaşılır mı?

### Eklenmesi gereken işler

1. **Hızlı başlangıç ve ön kontrol:** Python/işletim sistemi/ajan sürümleri,
   Core ve adapter uyumluluğu, hedef repo durumu, mevcut `.vcps/` kayıtları,
   yazma izinleri ve Codex sandbox/approval gereksinimleri için
   `doctor`/preflight komutu veya eşdeğer açık bir kontrol listesi sunulsun.
2. **Planla ve göster modu:** Kurulumdan önce eklenecek, kopyalanacak,
   symlink yapılacak veya mevcut olduğu için atlanacak yolları; Core
   sürümünü; adapter sürümünü; gereken izin değişikliklerini özetleyen
   salt-okunur `--dry-run`/`--plan` modu eklensin.
3. **Atomik kurulum ve kurtarma:** Birden çok dizine kopyalama sırasında
   hata oluşursa, önce geçici dizine kurup doğrula ve sonra atomik taşıma
   uygula ya da açık bir transaction manifestiyle yalnızca bu çalıştırmanın
   oluşturduğu yolları güvenli geri al. Önceden var olan kullanıcı
   dosyalarına dokunma. Hata raporunda hangi adımların tamamlandığı ve
   temizleme durumu yazsın.
4. **Tekrarlanabilir güncelleme:** Kurulu bileşenlerin sürüm/hash manifesti
   saklansın; `upgrade` kaynak ve hedef sürümü karşılaştırsın, değişen
   dosyaları önizlesin, kullanıcı düzenlemelerini saptasın ve üzerine yazma
   politikası uygulasın. Şema migrasyonu ile adapter/Core güncellemesi
   birbirinden ayrılıp uyumluluk tablosuna bağlansın.
5. **Doğrulama kapsamını genişletme:** Mevcut verify çıktısı dosya
   karşılaştırmasını bildiriyor. Claude kopya/symlink, Claude vendored Core,
   Codex repo ve Codex global kurulum için eksik/yabancı/değiştirilmiş dosya,
   bozuk symlink, sürüm uyuşmazlığı ve helper çalıştırılabilirliği
   denetlensin. Global Codex doğrulamasının `UNTRUSTED-CONTENT.md` ve tam
   kaynak ağacı dahil her kopyalanan dosyayı kapsadığı kanıtlansın.
6. **Kaldırma/onarım:** `uninstall` ve `repair` tasarlansın. Kaldırıcı yalnızca
   manifestte sahiplenilmiş, kurulumdan beri değişmemiş dosyaları silsin;
   kullanıcı değişikliklerini saklasın ve önizleme sunsun. Vendored Core ile
   proje `.vcps/` verileri farklı sahiplik sınıfları olarak ele alınsın.
7. **Symlink ve kaynak güveni:** Kaynak repo ile hedefin aynı yer/aynı repo
   olma, symlink hedefinin taşınması, dış kaynak yolu, Windows/Unix davranışı
   ve güvenilmeyen kaynak ağacı senaryoları açıkça ele alınsın.
8. **Dağıtım kanalı:** Paket yayımlamak karar ise sürüm imzalama/hash,
   kaynak doğrulama, changelog, desteklenen Python/OS aralığı ve kurulum
   komutu tanımlansın. Paket yayımlamak hedef değilse checkout tabanlı
   kurulum desteklenen resmi yöntem olarak quick-start'ta netleştirilsin.
9. **Codex bağımlılığını çözme:** `adapters/claude-code/` altından ortak
   yardımcıları çalıştırma bağımlılığı, agent-bağımsız ve sürümlenmiş ortak
   pakete taşınsın veya Codex'in kopyalanmış yardımcılarının aynı kaynakla
   üretilip test edildiği garanti edilsin. Sessiz kopya sapması riski
   kaldırılmalı.

### Fazlara etkisi

**Faz 1** hızlı başlangıç, ön kontrol ve kurulum planını; **Faz 2**
doğrulayıcı/CI'yi; **Faz 3** atomiklik, yükseltme, kaldırma, sürüm manifesti,
kurulum matrisinin tamamı ve ortak yardımcı paketini kapsar. Faz 3
başlamadan mevcut testlerde bulunmayan arıza enjeksiyonu ve kullanıcı
değişikliği senaryoları ayrıca eklenmelidir.

## 4. İnceleme turu 3 — Kanıt, güvenlik, birlikte çalışabilirlik ve yayın

### İncelenen soru

Faz çıkışları gerçek kullanıcı ve ajan davranışını, doğru kanıt sınıfını,
güvenlik sınırlarını ve sürüm kararını yeterli kapsamda gösteriyor mu?

### Eklenmesi gereken işler

1. **Tek komutlu tekrarlanabilir doğrulama:** Bütün yapısal ve simüle
   edilmiş suite'leri tek bir komutla çalıştıran üst seviye runner ekle;
   suite envanterini, kapsamı ve atlananları raporla. Test eklemeden
   kapsam iddiası yapılmasın; her suite'in `STRUCTURAL_TEST`,
   `SIMULATED_EXECUTION` veya `LIVE_ADAPTER_EXECUTION` sınırı görünür olsun.
2. **CI ve kanıt saklama:** Desteklenen Python/OS matrisinde test, şema ve
   örnek doğrulama, secret/dependency/supply-chain taraması çalışsın.
   CI çıktısı commit/revision'a bağlansın, saklama/erişim süresi belli olsun
   ve Gate 4/5 kayıtlarına taşınabilir kanıt URI/özeti sağlasın. CI
   başarısızlığını `NOT_RUN` veya kısmi olarak gizlemek mümkün olmasın.
3. **Doğrulayıcı kapsamının tamamlanması:** 14 validation maddesi için
   gereklilik bazlı test matrisi kur; her maddeye pozitif, negatif ve
   sınır vakası ekle. Özellikle ID çapraz referansları, append-only geçmiş,
   revision/staleness, gate applicability, insan kararının kimliği/scope'u,
   plan hash/fingerprint ve kayıtlar arası durum geçişleri tam denetlensin.
   JSON Schema gerçek bir 2020-12 uygulamasıyla doğrulansın; özel/stdlib
   alt-küme doğrulaması tek kanıt olarak kullanılmasın.
4. **Model davranışı değerlendirme disiplini:** Mevcut anti-gaming diff
   kataloğuna ek olarak çoklu ifade, çoklu bağlam, yanlış pozitif/negatif,
   açık talimat enjeksiyonu ve ret/izin sınırları kapsansın. Kör rubric,
   model/sürüm, prompt, araç yeteneği ve tekrarlanabilirlik kaydı tutulsun.
   Tek başarılı örnek genelleştirilmiş güvence sayılmasın.
5. **Canlı adaptör kabul matrisi:** Her adaptör × workflow × mutasyon türü
   için keşif, onay, yazma, hata/ret, resume, idempotency, revision
   invalidation, doğrulama, Gate 4/5 independence ve handoff testleri
   planlansın. İnsan onayı gereken gerçek işlemlerde sentetik karar
   üretilmesin; insan katılımı yoksa açık `BLOCKED` kanıtı kaydedilsin.
6. **Cross-agent tam devir:** Minimum dosya/handoff okuma kanıtı, tam
   beceri yükleme, akışın sürdürülmesi, gate kaydı üretimi ve checkpoint
   devrinden ayrı raporlansın. Claude→Codex ve Codex→Claude yönlerinin her
   biri için temiz oturum ve farklı proje örneği bulunsun.
7. **Güvenlik tehdit kapsamı:** `evaluation/security-audit.md`'de açık kalan
   tüm mutasyon yolları için tehdit modeli/deney listesi çıkar. Provider
   yanıtı, webhook, dosya, CI logu ve model çıktısı gerçek ingestion
   sınırlarından denenmeli. İşletim sistemi izinleri, hedef Git yapılandırması,
   symlink/rename yarışı, büyük girdiler, gizli veri sızıntısı, tool denial
   sonrası iddia bütünlüğü ve bağımlılık güncelleme zinciri kapsansın.
8. **Yayın ve destek sınırı:** Adapter/Core/schema uyumluluk matrisi,
   sürüm yükseltme/downgrade kuralları, deprecation, migration yedeği,
   release artifact bütünlüğü, desteklenen platformlar ve bilinen
   sınırlamalar yayın kontrolüne eklensin. Gate 6 için gerekli Gate 1–5
   kayıtları, HC-10 koşulları ve gözlem penceresi otomatik raporlanabilir;
   onay yalnızca yetkili insandan gelsin.
9. **Sürekli bakım:** CI/toolchain güncellemeleri, Core sürüm değişiklikleri,
   şema migration'ları ve prompt/adapter değişiklikleri için hangi suite'in
   yeniden çalışacağı tanımlansın. Başarılı eski kanıt, yeni revision veya
   yeni runtime için taze kanıt gibi gösterilmesin.

### Fazlara etkisi

Faz 2 doğrulayıcı ve CI'yi; Faz 4 canlı, çoklu adaptör kabulini; Faz 5
güvenlik kapsamı, yayın kapısı ve bakım politikasını sahiplenir. Canlı
kanıt bulunmaması başarısızlık değildir ama daha yüksek kanıt iddiasını
engeller ve ilgili fazın sınırında kayıtlı kalır.

## 5. Güncellenmiş Faz 0–5 planı

### Faz 0 — Ürün kapsamı, Core kapıları ve izlenebilirlik

**Amaç:** Hangi kullanıcı problemi çözüldüğünü, hangi Core hükümlerinin
bağlayıcı olduğunu ve başarı kanıtının ne olacağını sabitlemek.

**İşler:** Kullanıcı profilleri ve quick-start yolculuk haritası; Faz 0–5
kapsam kartları; Gate → workflow → schema → validator → scenario → evidence
matrisi; gate recovery/ratification incelemesi; R sınıfı ve bağımsızlık
örnekleri; ürün kabulü ile yayın kararının ayrıştırılması; adapter/Core/schema
destek matrisi ve karar kaydı.

**Çıkış kanıtı:** Her açık Core gerekliliğinin sahibi ve test/kayıt hedefi
var; tartışmalı recovery alanları `PARTIAL`/açık olarak işaretli; her fazın
Gate ve insan checkpoint gereksinimi tanımlı; README ile roadmap arasındaki
durum iddiaları tutarlı. Tam requirement-level validator kapsamı Faz 2'de
tamamlanacak.

**Durum: TAMAMLANDI (planlama/baseline kapsamı).** Ayrıntılı kapsam ve
izlenebilirlik kaydı [`phase-0-charter.md`](phase-0-charter.md) içindedir.

**Kapılar:** Gate 1 `PASS`; Gate 2 `PASS` veya gerekçeli `PARTIAL` (karar
gereken her madde için HC); Gate 3 incelemesi bu plan değişikliğinin
kapsamına göre.

### Faz 1 — Başlangıç, ön kontrol ve ilk kurulum

**Amaç:** Yeni kullanıcının repo, ajan, Core ve adapter uyumunu anlayıp
kuruluma güvenle başlaması.

**İşler:** Claude/Codex quick-start; açık önkoşullar; `doctor`/preflight;
kurulum planı/dry-run; hedef repo ve mevcut `.vcps/` durumu özeti; Codex
sandbox/approval kılavuzu; copy/symlink ve `--vendor-core` seçimi; daraltılmış
skill kurulumu bağımlılıklarının açıklaması; kurulum sonrası ilk doğrulama ve
başarısızlık çözüm rehberi; temiz proje ve mevcut proje için ayrı akışlar.

**Çıkış kanıtı:** Temiz, geçici repoda her iki ajanın kurulum adımları yeni
kullanıcı tarafından tamamlanabiliyor; ön kontrol zararsız; önizleme ile
gerçek değişiklik birebir tutarlı; kullanıcıya Core/adapter/sandbox
uyumsuzluğu işlemden önce bildiriliyor.

**Kapılar:** Gate 1, Gate 3 (kurulum değişikliği/anti-gaming), Gate 4
(önkontrol ve kurulum doğrulaması), ilgili yüzey varsa Gate 5.

### Faz 2 — Tekrarlanabilir doğrulama, Core validator ve CI

**Amaç:** Repo ve örnek projeler için her geliştiricinin ve CI'ın aynı
sonucu üretebildiği kanıt hattı kurmak.

**İşler:** Üst seviye test runner; CI workflow; Python/OS matrisi; gerçek
JSON Schema 2020-12 validator; validation.md 14 maddesinin izlenebilir
kapsama/test matrisi; örnek proje ve migration testleri; gate/evidence/
revision/staleness/independence çapraz kontrolleri; dependency ve secret
tarama; CI artefakt saklama ve E3 kanıt referans formatı; required ve
optional check ayrımının baseline'a bağlanması.

**Çıkış kanıtı:** Temiz checkout'ta tek komut tüm yerel suite'leri çalıştırır;
CI aynı işi yapar; her doğrulama maddesi pozitif/negatif/sınır testiyle
kapsanır veya gerekçeli açık kalır; revision'a bağlı retrievable E3 kaydı
üretilebilir; başarısızlık ve atlanan kontrol açık görünür.

**Kapılar:** Gate 2 (CI ve validator mimarisi), Gate 3, Gate 4; dependency/
CI değişikliklerinde Gate 5; risk sınıfı gerektiriyorsa bağımsız inceleme.

### Faz 3 — Kurulum yaşam döngüsü ve taşınabilir adaptör mimarisi

**Amaç:** Kurulumu güvenli, tekrarlanabilir, güncellenebilir ve geri
alınabilir yapmak; Codex'in Claude kaynak yollarına bağımlılığını çözmek.

**İşler:** Installer manifesti; tüm platform/adapter/scope kombinasyonları;
atomik staging ve rollback; install verify; upgrade/diff; kullanıcı
düzenlemesini koruma; güvenli uninstall/repair; Core pin/hash ve adapter
uyumluluk kontrolü; schema migration önizleme/yedek/rollback; symlink
taşınma davranışı; ortak yardımcıların agent-bağımsız paketlenmesi veya
tek kaynaklı üretimi; paket kanalı kararı, imza/hash ve destek politikası.

**Çıkış kanıtı:** Kurulum, yarıda kesilme, tekrar, upgrade, kullanıcı
değişikliği, verify ve uninstall senaryoları geçici hedeflerde kanıtlı;
önceden var olan yollar değişmiyor; hedef proje verisi kurulum bileşenleri
sanılarak silinmiyor; Codex helper sürümü tek kaynağa bağlı.

**Kapılar:** Gate 1 (DX kabulü), Gate 2 (sahiplik/rollback/güven sınırları),
Gate 3, Gate 4 ve installer'ın kaynak/target işlemleri için Gate 5.

### Faz 4 — Adaptör ve iş akışı canlı kabulü

**Amaç:** Yapısal olarak doğru becerilerin gerçek ajan oturumlarında
beklenen izin ve kanıt davranışını gösterdiğini doğrulamak.

**İşler:** Claude × Codex × dokuz beceri için kabul matrisi; invoke/load,
read-only keşif, risk escalation, kullanıcı onayı, mutasyon, ret/denial,
hata raporlama, resume/idempotency, revision invalidation, gate kaydı,
handoff ve untrusted-content davranışı; bağımsız Gate 4/5 örnekleri;
Claude/Codex karşılıklı tam devir; sürüm değişikliği sonrası smoke kabulü.

**Çıkış kanıtı:** Her kombinasyon `LIVE`, `BLOCKED` veya `NOT_APPLICABLE`
olarak kanıt/reason code ile kayıtlı; `LIVE` iddiası kullanılan runtime,
adapter revision, prompt/skill, target revision ve gerçek tool output ile
bağlı; insan checkpoint'i insandan gelmiş; partial coverage net belirtilmiş.

**Kapılar:** Gate 3; Gate 4 zorunlu ve gereken independence/evidence tier'da;
her temas edilen güvenlik kategorisi için Gate 5. Gate 6 yayın varsa ayrıca.

### Faz 5 — Güvenlik güvencesi, yayın hazırlığı ve bakım

**Amaç:** Kalan güvenlik risklerini sınırlamak, yayın birimini insan kararıyla
kontrollü çıkarmak ve kanıtın zamanla eskimesini yönetmek.

**İşler:** Kalan §31/mutasyon yüzeyi tehdit incelemesi; provider/webhook/file/
CI/model ingestion deneyleri; tool denial sonrası iddia bütünlüğü; secret/
dependency/artifact tedarik zinciri; desteklenen ortamda production-config
review; sürüm uyumluluk/deprecation/migration/downgrade politikası; release
checklist ve Gate 6 raporu; release artifact provenance; observation window
ve E5 toplama; bakımda hangi değişikliklerin hangi suite/kanıtı invalid kıldığı.

**Çıkış kanıtı:** Kapsamlı tehdit listesinde her item kapalı, kabul edilmiş
veya gerekçeli olarak ertelenmiş; yeni security finding baseline'a göre
değerlendirilmiş; release revision'daki gerekli Gate 1–5 sonuçları
doğrulanmış; HC-10 olumlu ve koşulları tamamlanmış; yayın sonrası gözlem
kanıtının sahibi ve takvimi belirlenmiş.

**Kapılar:** Gate 5 ve her release birimi için Gate 6. Gate 6 yalnızca gerçek
yetkili insanın olumlu kararıyla `PASS` olabilir.

## 6. Bağımlılık ve öncelik sırası

`Faz 0 → Faz 1 → Faz 2 → Faz 3 → Faz 4 → Faz 5` ana sırasıdır. Faz 1'in
quick-start taslağı Faz 0 sırasında kullanıcı doğrulaması için erken
hazırlanabilir. Faz 2'nin küçük runner/CI altyapısı Faz 1 testlerini
doğrulayabilir; ancak tam validator kapsamı Gate izlenebilirlik matrisi
çıktısına dayanmalıdır. Faz 3'ün mimari kararı Codex helper bağımlılığı ve
paket hedefini karara bağlamadan dondurulmamalıdır. Faz 4 gerçek insan
onayına bağlı senaryolarda bekleyebilir; diğer read-only akışlar paralel
kabul edilebilir. Faz 5 sürekli güvenlik bakımının temelini kurar; yayın
kararı her release için yeniden Gate 6'dan geçer.

## 7. Sınırlar ve açık kararlar

- Bu inceleme mevcut çalışma ağacını okuma ve yeni plan belgesi yazma
  kapsamındadır. Kurulum mimarisi, Core kapıları veya adapter kodu bu
  çalışma kapsamında değiştirilmemiştir.
- Kullanıcıya ait önceden var olan çalışma ağacı değişiklikleri korunmuştur;
  `evaluation/completion-roadmap.md` üzerinde değişiklik bulunduğu için bu
  plan ayrı dosyada tutulmuştur.
- Paket yayımlama bir ürün kararıdır. Faz 3'te checkout tabanlı resmi
  kurulum ile yayımlanmış paket seçeneği karşılaştırılmalı; hedef
  varsayılmamalıdır.
- `L3` seviyesi için gereken E3/HC-08 örneği canlı altyapı ve yetkili insan
  kararına bağlıdır. Sentetik fixture bu checkpoint'leri gerçekmiş gibi
  kapatamaz.
