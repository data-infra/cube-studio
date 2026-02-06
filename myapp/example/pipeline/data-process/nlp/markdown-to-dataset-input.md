

# Oracle ZFS Storage Appliance ZS11-2

Oracle ZFS Storage Appliance 系统可提供强大的 NAS、SAN、对象存储和云存储功能，以超强的企业存储性能满足严苛的企业应用与负载要求。Oracle ZFS Storage Appliance 系统与 Oracle 数据库、Oracle 集成系统以及 Oracle 公有云深度集成，是一种 Oracle 集成设计的存储系统，可以实现其它同类竞争产品无法企及的、最大化的 Oracle 软件投资回报。如果您需要加快关键型应用的速度，提高业务与 IT 效率，Oracle ZFS Storage Appliance 系统可以通过节省资源、降低风险和总拥有成本 (TCO)，使用户获得实质性的收益。

## 超强的企业存储性能

Oracle ZFS Storage Appliance 系统基于先进的软硬件架构构建而成。它拥有现代企业硬件系统中常见的高度智能的多线程 SMP 存储操作系统，助您在不牺牲性能的情况下高效运行多种负载和高级数据服务。此超强系统中独有的混合存储池设计可自动将数据缓存到动态随机存取存储器 (DRAM) 或闪存缓存中，以此实现出色性能和卓越效率，同时确保数据安全地存储在可靠的大容量固态驱动器 (SSD) 或硬盘驱动器 (HDD) 存储中。在混合存储池设计下，高频访问数据将主要通过缓存进行访问（占比高达 90%），能够以极高的吞吐量和极低的延迟满足严苛负载要求，加快应用速度。

Oracle ZFS Storage Appliance 还集成了高可用性 (HA) 特性，例如通过双活控制器集群实施故障切换，通过自我修复文件系统架构确保端到端的数据完整性。得益于高可靠性与丰富的企业级数据服务，Oracle ZFS Storage Appliance 系统是严苛企业存储应用的理想之选。

<div style="text-align: center;"><img src="imgs/img_in_image_box_949_116_1100_477.jpg" alt="Image" width="12%" /></div>


## 主要业务优势

- 超强性能，可加快 Oracle 数据库和应用运行速度

- 充分提升 Oracle 软件的投资回报

- 即时、零开销的快照和克隆且支持高度虚拟化的环境，可加快开发和测试速度

- 在一个系统中整合 NAS、SAN 和对象存储，可降低 IT 复杂性、减少管理工作并节省成本

- 同时支持生产、开发测试和数据保护负载，可提高 IT 敏捷性

- 细粒度加密，可降低安全风险和成本

- 出色的性价比和极低的每TB存储成本，可降低TCO

<div style="text-align: center;">图1. 以 DRAM 为中心的架构</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_111_144_823_452.jpg" alt="Image" width="58%" /></div>


## 卓越效率

Oracle ZFS Storage Appliance 系统提供了一组先进的管理和分析工具，支持存储管理员快速供应和管理存储，进行故障排除。利用直观的浏览器用户界面 (BUI) 或命令行界面 (CLI)，您可以快速部署强大的高级数据服务，包括无限制的快照、克隆、精简供应、五种压缩算法以及复制。

<div style="text-align: center;">图2. 管理软件状态视图</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_107_702_884_1388.jpg" alt="Image" width="63%" /></div>


Oracle ZFS Storage Appliance 系统的 DTrace Analytics 特性则支持实时分析和监视，您可以精细地查看磁盘、闪存、控制器 CPU、网络、缓存、虚拟机 (VM) 等等的统计信息，将从客户端网络接口到存储设备之间的一切活动都尽收眼底。

<div style="text-align: center;">图 3. DTrace Analytics 示例：每磁盘每秒 I/O 操作数</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_108_232_833_682.jpg" alt="Image" width="59%" /></div>


得益于这种精细的可见性（I/O、虚拟机或可插拔数据库级），您可以快速识别和解决瓶颈问题，出色地完成系统性能调优和故障排除，尤其是在大规模虚拟服务器环境下。无论是在 Oracle 的内部 IT 环境下还是在独立测试中，Oracle ZFS Storage Appliance 系统都表现出了出色的管理效率：不仅简化了存储管理，大幅提高了单个管理员可管理的数据量，还显著降低了运营成本。

## Oracle 数据库集成

Oracle ZFS Storage Appliance 系统与 Oracle 数据库深度集成，大幅提高了性能和效率，降低了 TCO。得益于统一设计、开发、测试和软硬件支持，Oracle 集成存储系统能够以多重独有功能大幅提升 Oracle 软件的运行速度和效率。Oracle ZFS Storage Appliance 系统与 Oracle 软件采用集成设计，以成熟的解决方案和优秀实践做后盾，能够消除整个系统配置过程中的不确定性，确保部署成功。其特性包括：

## • Oracle 智能存储协议

Oracle Intelligent Storage Protocol（Oracle 智能存储协议，简称 OISP）是与 Oracle ZFS Storage Appliance 系统协同运行的 Oracle Database 12c（及更高版本）的专有存储协议。它支持存储系统以空前的洞察水平从 Oracle 数据库接收关于数据流的线索。换言之，每个读取和写入操作的类型和重要性等信息将从 Oracle 数据库发送到 Oracle ZFS Storage Appliance 系统，然后 Oracle ZFS Storage Appliance 系统会智能地处理 I/O，通过自动、动态的自我调优来实现最优性能。由此，最关键的数据库操作将被赋予较高的优先级，您无需手动调优就能加快数据库运行速度。此外，OISP 还能减少高达 90% 的繁琐的手动操作，降低人为错误风险，进一步加快供应速度。

自我调优功能还可以防止 Oracle Recovery Manager (Oracle RMAN) 备份等高带宽操作产生的数据块占用 DRAM 缓存中的关键空间，从而最大限度加快延迟敏感型数据库操作速度。而且，借助 Automatic Workload Repository（自动负载信息库，简称 AWR）感知的扩展分析功能，IT 管理员可以按数据库名称、数据库函数和数据库文件类型查看 OISP 操作，查看 I/O 操作的详细信息，包括可插拔数据库级信息，借此捕获关于数据库操作性质的宝贵洞察，加快故障排除速度，改善故障排除效果，尤其是在复杂的多租户 Oracle Database 环境下。

<div style="text-align: center;">图 4. Oracle Database 19c（及更高版本）和 Oracle 智能存储协议</div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_152_344_710_693.jpg" alt="Image" width="45%" /></div>


## Oracle 混合列压缩

Oracle 数据库的 Oracle Hybrid Columnar Compression（Oracle 混合列压缩）特性可将 Oracle 数据库的数据仓储、分析和归档等负载的数据量降低到五十分之一至十分之一，将查询速度提高 3 至 8 倍。这一专为 Oracle 数据库打造的数据压缩解决方案系 Oracle 存储产品独有，可大幅降低您的存储空间需求和相关数据中心成本。此外，Oracle Database 12c（及更高版本）的 Automatic Data Optimization（自动数据优化）特性支持您按照实际数据使用情况，设置 Oracle 混合列压缩和数据分层的启动策略，从而自动管理整个数据生命周期。

## • 适用于 Oracle ZFS 存储系统的 Oracle Enterprise Manager 插件

由 Oracle Enterprise Manager Plug-in for Oracle Systems Infrastructure 提供对 Oracle ZFS Storage Appliance 的支持，它不仅能提供跨整个企业的端到端存储管理可见性，还支持共享文件系统、LUN 或项目级的监视和供应。该插件能够简化实施、提高可见性和提升整体管理效率。

## 云集成

传统的存储架构需要额外配备适当的资源来支持高度虚拟化的动态云负载。相比之下，Oracle ZFS Storage Appliance 系统具有以下特点：

## • 云架构

凭借对称多处理 (SMP) 操作系统 (OS) 以及混合存储池技术的架构优势，Oracle ZFS Storage Appliance 可为本地和私有云混合负载提供持续的高性能支持。

## ORACLE

## 云托管

借助 RESTful API，Oracle ZFS Storage Appliance 系统支持 OpenStack 和 Oracle Enterprise Manager Cloud Control 等云管理框架，您可以将其集成到任意环境。

## 云集成

很多供应商都没有自己的公有云，而借助 Oracle ZFS Storage Appliance，您可以将您的本地存储系统与 Oracle 公有云集成，更轻松地开启上云之旅。Oracle ZFS Storage Appliance 的集成式云快照备份特性可降低本地部署成本，提供灵活的归档和恢复选项。您可以通过 OCI Marketplace 获取 Oracle ZFS Storage 映像，将负载和数据迁移到 Oracle 云。

## 架构和配置选项

Oracle ZFS Storage Appliance 系统在架构上包含三个主要组件：

## 软件

独有的智能多线程 SMP 存储操作系统，可提供多种企业级数据服务和可靠的数据保护；通过混合存储池技术可管理动态缓存。基础系统即包含大多数数据服务（包括 DTrace Analytics 特性）。

## 控制器

一个强大、可靠的基于 Oracle 经济高效的企业级 x86 服务器的存储控制器，可提供强大的计算性能和大容量 DRAM。双控制器集群配置（可选）可通过快速故障切换特性实现高可用性。

## 存储

企业级存储机柜，支持全闪存存储、全 HDD 存储或 SSD 与 HDD 混合存储，您可以按需优化存储池，满足您多样化的性能和容量需求。这些存储采用了新一代的 SAS HDD 和 SSD，可通过读写闪存加速器确保实现高性能和高可用性。

Oracle ZFS Storage Appliance ZS11-2 上提供一种单控制器型号，适用于性能密集型环境。如果用户需要超强可扩展性，可以为 ZS11-2 配置不同数量的 DRAM，或者添加额外的 HBA 来扩展存储空间，最多可支持 48 个硬盘柜。

Oracle ZFS Storage Appliance 采用智能存储操作系统、混合存储池技术、企业 SAS 磁盘或闪存机柜，支持高性能 NAS、SAN 和对象存储访问，可满足特定环境下的性价比要求。

## 机柜式存储系统

Oracle ZFS Storage Appliance Racked System（Oracle ZFS 机柜式存储系统）是经过全面测试的预组装系统，已内置复制、克隆和加密许可，无需您额外支付许可费用。这种预配置系统可大幅缩短部署和实施时间，优化性能，提高可用性，降低风险和 TCO。针对连接到 Oracle Exadata 系统的关键业务 RMAN 备份场景，您还可以选择含 100GbE 网络接口和交换机的配置选项。

如果您使用 Oracle ZFS 机柜式存储系统来备份 Oracle Exadata 等 Oracle 集成系统，您可以获得 Oracle 白金服务，通过 24x7 远程故障监视、快捷响应和补丁部署服务来最大限度延长正常运行时间，快速解决问题。如需了解 Oracle 白金服务的最低配置要求，请咨询您的客户代表。

## 可选软件

除了基础系统附带的丰富的软件套件外，您还可以购买单独许可的软件特性，例如远程复制、克隆和加密。Oracle ZFS Storage Appliance ZS11-2 机柜式存储系统中已附带这些许可证。

<div style="text-align: center;">Oracle ZFS 存储系统规格</div>



<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'></td><td style='text-align: center;'>Oracle ZFS ZS11-2 存储系统</td><td style='text-align: center;'>Oracle ZFS ZS11-2 机柜式存储系统</td></tr><tr><td style='text-align: center;'>配置</td><td style='text-align: center;'>模块配送</td><td style='text-align: center;'>预组装、测试和机柜配送</td></tr><tr><td style='text-align: center;'>架构</td><td style='text-align: center;'>采用外部存储机柜的单控制器或者双控制器HA集群</td><td style='text-align: center;'>采用外部存储机柜的双控制器HA集群</td></tr><tr><td style='text-align: center;'>处理器</td><td style='text-align: center;'>4 颗 32 核 3.2 GHz（最高 4.4 GHz）AMD® EPYC® 处理器（每两个控制器）</td><td style='text-align: center;'>4 颗 32 核 3.2 GHz（最高 4.4 GHz）AMD® EPYC® 处理器（每两个控制器）</td></tr><tr><td style='text-align: center;'>DRAM 缓存</td><td style='text-align: center;'>最高 4.6 TB（每两个控制器）</td><td style='text-align: center;'>最高 4.6 TB（每两个控制器）</td></tr><tr><td style='text-align: center;'>读取闪存缓存</td><td style='text-align: center;'>最高 1.4 PB</td><td style='text-align: center;'>最高 1.4 PB</td></tr></table>

## 存储配置


<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'></td><td style='text-align: center;'>Oracle ZFS ZS11-2 存储系统</td><td style='text-align: center;'>Oracle ZFS ZS11-2 机柜式存储系统</td></tr><tr><td style='text-align: center;'>磁盘存储选项(原始容量)</td><td style='text-align: center;'>• 520 TB 至最大支持 30 PB• 最多 48 个磁盘柜, 每个磁盘柜配备 20 或 24 个 HDD• 每个磁盘柜配备 20 个 HDD, 可选择 1 到 4 个读/写 SSD 加速器</td><td style='text-align: center;'>• 520 TB 至最大支持 30 PB• 最多 48 个磁盘柜, 每个磁盘柜配备 20 或 24 个 HDD• 每个磁盘柜配备 20 个 HDD, 可选择 1 到 4 个读/写 SSD 加速器</td></tr><tr><td style='text-align: center;'>闪盘存储选项(原始容量)</td><td style='text-align: center;'>• 153 TB 至最大支持 8.8 PB• 1 到 48 个闪盘柜, 每个闪盘柜配备 20 或 24 个 SSD• 每个闪盘柜配备 20 个 SSD, 可选择 1 到 4 个写 SSD 加速器</td><td style='text-align: center;'>• 153 TB 至最大支持 8.8 PB• 1 到 48 个闪盘柜, 每个闪盘柜配备 20 或 24 个 SSD• 每个闪盘柜配备 20 个 SSD, 可选择 1 到 4 个写 SSD 加速器</td></tr><tr><td style='text-align: center;'>存储柜选项</td><td colspan="2">磁盘存储柜:• Oracle 存储柜 DE3-24C: 26 TB SAS-3 3.5 英寸 7200 RPM HDD, 7.68 TB SAS-3 3.5 英寸 SSD, 200 GB SAS-3 3.5 英寸 SSD• Oracle 存储柜 DE3-24C: 22 TB SAS-3 3.5 英寸 7200 RPM HDD, 7.68 TB SAS-3 3.5 英寸 SSD, 200 GB SAS-3 3.5 英寸 SSD• Oracle 存储柜 DE3-24P: 1.2 TB SAS-3 2.5 英寸 10000 RPM HDD, 7.68 TB SAS-3 2.5 英寸 SSD, 200 GB SAS-3 2.5 英寸 SSD闪盘存储柜:• Oracle 存储柜 DE3-24P: 7.68 TB SAS-3 2.5 英寸 SSD</td></tr></table>

注意：ZS11-2 系统的磁盘（HDD 和 SSD）总数最多为 1152。

<div style="text-align: center;">标准接口和可选接口</div>



<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'>接口</td><td style='text-align: center;'>说明</td></tr><tr><td style='text-align: center;'>集成网络</td><td style='text-align: center;'>仅管理端口</td></tr><tr><td style='text-align: center;'>可选网络连接</td><td style='text-align: center;'>10GBASE-T，10Gb/25Gb/40Gb/100GbE（铜缆/光纤），32Gb光纤通道，100Gb以太网交换机</td></tr><tr><td style='text-align: center;'>可选SAN/磁带备份HBA</td><td style='text-align: center;'>双通道32Gb FC HBA</td></tr></table>

<div style="text-align: center;">单系统最高端口数</div>



<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'></td><td style='text-align: center;'>Oracle ZFS ZS11-2 存储系统</td><td style='text-align: center;'>Oracle ZFS ZS11-2 机柜式存储系统</td></tr><tr><td style='text-align: center;'>10GBASE-T / 10GbE / 25GbE / 32Gb FC / 40GbE / 100GbE</td><td style='text-align: center;'>48/24/24/24/24/16</td><td style='text-align: center;'>48/24/24/24/24/16</td></tr></table>

注意：所有端口全速并行可能受限

环境


<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'>规格</td><td style='text-align: center;'>说明</td></tr><tr><td style='text-align: center;'>工作温度</td><td style='text-align: center;'>5℃至35℃（41°F至95°F）</td></tr><tr><td style='text-align: center;'>非工作温度</td><td style='text-align: center;'>-40℃至70℃（-41°F至158°F）</td></tr><tr><td style='text-align: center;'>工作相对湿度</td><td style='text-align: center;'>10%至90%，无冷凝</td></tr><tr><td style='text-align: center;'>非工作相对湿度</td><td style='text-align: center;'>93%，无冷凝</td></tr><tr><td style='text-align: center;'>海拔（工作）</td><td style='text-align: center;'>0 - 3050米（0 - 10007英尺）；900米以上时，每升高300米，最高环境温度降低1℃（中国相关法规可能限定最高安装海拔为2000米）。</td></tr><tr><td style='text-align: center;'>噪音</td><td style='text-align: center;'>工作时A型加权噪声为8.1B，闲置时A型加权噪声为5.8B（声功率测量值）。请查看您安装Oracle设备当地对工作场所噪音级别暴露限值的相关规定，并适当使用个人防护设备。</td></tr><tr><td style='text-align: center;'>其他</td><td style='text-align: center;'>符合美国采暖、制冷与空调工程师学会(ASHRAE)数据中心Class A2标准</td></tr></table>

## 功率和散热量


<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'>组件</td><td style='text-align: center;'>说明</td><td style='text-align: center;'>典型值</td><td style='text-align: center;'>最大值</td></tr><tr><td rowspan="2">Oracle ZFS ZS11-2 存储系统</td><td style='text-align: center;'>功率</td><td style='text-align: center;'>823 W</td><td style='text-align: center;'>978 W</td></tr><tr><td style='text-align: center;'>散热量</td><td style='text-align: center;'>2808 BTU/小时</td><td style='text-align: center;'>3336 BTU/小时</td></tr></table>


<table border=1 style='margin: auto; width: max-content;'><tr><td rowspan="2">Oracle 存储硬盘柜 DE3-24C</td><td style='text-align: center;'>功率</td><td style='text-align: center;'>256 W</td><td style='text-align: center;'>285 W</td></tr><tr><td style='text-align: center;'>散热量</td><td style='text-align: center;'>875 BTU/小时</td><td style='text-align: center;'>973 BTU/小时</td></tr><tr><td rowspan="2">Oracle 存储硬盘柜 DE3-24P</td><td style='text-align: center;'>功率</td><td style='text-align: center;'>248 W</td><td style='text-align: center;'>298 W</td></tr><tr><td style='text-align: center;'>散热量</td><td style='text-align: center;'>846 BTU/小时</td><td style='text-align: center;'>1017 BTU/小时</td></tr><tr><td rowspan="2">Oracle ZFS ZS11-2 机柜式存储系统</td><td style='text-align: center;'>功率</td><td style='text-align: center;'>3784 W</td><td style='text-align: center;'>5714 W</td></tr><tr><td style='text-align: center;'>散热量</td><td style='text-align: center;'>12912 BTU/小时</td><td style='text-align: center;'>19497 BTU/小时</td></tr></table>

## 物理规格


<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'>组件</td><td style='text-align: center;'>说明</td><td style='text-align: center;'>最大值</td></tr><tr><td rowspan="4">Oracle ZFS ZS11-2 存储系统(仅控制器)</td><td style='text-align: center;'>高度</td><td style='text-align: center;'>86.9 毫米 (3.42 英寸) 2U (机架单元)</td></tr><tr><td style='text-align: center;'>宽度</td><td style='text-align: center;'>445.0 毫米 (17.52 英寸)</td></tr><tr><td style='text-align: center;'>深度</td><td style='text-align: center;'>756 毫米 (29.76 英寸)</td></tr><tr><td style='text-align: center;'>重量</td><td style='text-align: center;'>满配时 34 千克 (76 磅)</td></tr><tr><td rowspan="4">Oracle 存储硬盘柜 DE3-24C(硬盘满载)</td><td style='text-align: center;'>高度</td><td style='text-align: center;'>175 毫米 (6.89 英寸) 4U (机架单元)</td></tr><tr><td style='text-align: center;'>宽度</td><td style='text-align: center;'>483 毫米 (19 英寸)</td></tr><tr><td style='text-align: center;'>深度</td><td style='text-align: center;'>630 毫米 (24.8 英寸)</td></tr><tr><td style='text-align: center;'>重量</td><td style='text-align: center;'>46 千克 (101.41 磅)</td></tr><tr><td rowspan="4">Oracle 存储硬盘柜 DE3-24P(硬盘满载)</td><td style='text-align: center;'>高度</td><td style='text-align: center;'>86.9 毫米 (3.4 英寸) 2U (机架单元)</td></tr><tr><td style='text-align: center;'>宽度</td><td style='text-align: center;'>483 毫米 (19 英寸)</td></tr><tr><td style='text-align: center;'>深度</td><td style='text-align: center;'>630 毫米 (24.8 英寸)</td></tr><tr><td style='text-align: center;'>重量</td><td style='text-align: center;'>24 千克 (52.91 磅)</td></tr></table>

<div style="text-align: center;">Oracle ZFS 存储系统软件</div>



<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'>包含的特性</td><td style='text-align: center;'>详细说明</td></tr><tr><td style='text-align: center;'>Oracle 智能存储协议</td><td style='text-align: center;'>Oracle Database 19c（及更高版本）可将关于各 I/O 操作的元数据发送给 Oracle ZFS Storage Appliance 系统，使该系统能够动态地自我调优，实现最佳性能；提供数据库级和可插拔数据库级的可见性，以及切实可行的洞察。</td></tr><tr><td style='text-align: center;'>文件系统</td><td style='text-align: center;'>Oracle Solaris ZFS（128 位寻址）</td></tr><tr><td style='text-align: center;'>文件级协议</td><td style='text-align: center;'>NFS v2/v3/v4/v4.1、SMB1/2/2.1/3/3.1、HTTP、WebDAV、FTP/SFTP/FTPS</td></tr><tr><td style='text-align: center;'>块级协议</td><td style='text-align: center;'>ISCSI、光纤通道</td></tr><tr><td style='text-align: center;'>对象级协议</td><td style='text-align: center;'>Oracle OCI、Amazon S3 以及基于 HTTP 或 HTTPS 实现 Swift 兼容的对象存储</td></tr><tr><td style='text-align: center;'>云集成</td><td style='text-align: center;'>云快照备份（ZFS 或 TAR 格式），位于本地的 OCI 兼容的集成式对象存储，位于 OCI Marketplace 的 Oracle ZFS 存储</td></tr></table>


<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'>数据压缩</td><td style='text-align: center;'>五种压缩选项，可在数据精简与性能之间取得平衡</td></tr><tr><td style='text-align: center;'>混合列压缩</td><td style='text-align: center;'>静态 Oracle 数据库数据可压缩至原始的五十分之一至十分之一，从而将 Oracle 数据库中的数据仓库和长期存储信息的存储空间减少为五分之一至三分之一</td></tr><tr><td style='text-align: center;'>重复数据消除</td><td style='text-align: center;'>安装有元数据 SSD 时，支持内联式块级重复数据消除</td></tr><tr><td style='text-align: center;'>监视</td><td style='text-align: center;'>DTrace Analytics（用于系统调优和调试）；信息板（监视关键系统性能指标）；Oracle Enterprise Manager 插件</td></tr><tr><td style='text-align: center;'>自动化的可维护性</td><td style='text-align: center;'>提供“呼叫总部”功能，支持自动创建案件和可配置警报</td></tr><tr><td style='text-align: center;'>RAID</td><td style='text-align: center;'>条带化、镜像、三重镜像、单奇偶校验、双奇偶校验、三奇偶校验、宽条带化</td></tr><tr><td style='text-align: center;'>远程管理</td><td style='text-align: center;'>HTTPS、SSH、SNMP v1/v2c/v3、IPMI、RESTful API</td></tr><tr><td style='text-align: center;'>快照</td><td style='text-align: center;'>只读，可还原</td></tr><tr><td style='text-align: center;'>目录服务</td><td style='text-align: center;'>NIS、AD、LDAP</td></tr><tr><td style='text-align: center;'>数据安全性</td><td style='text-align: center;'>校验和数据及元数据、自动数据验证、病毒隔离</td></tr><tr><td style='text-align: center;'>网络服务</td><td style='text-align: center;'>NTP、DHCP、SMTP</td></tr><tr><td style='text-align: center;'>备份</td><td style='text-align: center;'>NDMP v3/v4、ZFS NDMP</td></tr><tr><td style='text-align: center;'>本地复制</td><td style='text-align: center;'>在同一 Oracle ZFS Storage Appliance 配置（单机或集群）下复制，或者复制到 OCI 中的 Oracle ZFS-HA Storage</td></tr><tr><td style='text-align: center;'>QoS/节流</td><td style='text-align: center;'>通过限制 NFS、SMB 和 LUN I/O 用量来更加有效地平衡系统资源</td></tr></table>


<table border=1 style='margin: auto; width: max-content;'><tr><td style='text-align: center;'>单独授予许可的特性</td><td style='text-align: center;'>详细说明</td></tr><tr><td style='text-align: center;'>克隆</td><td style='text-align: center;'>可写入快照（包含在机柜式系统配置中）</td></tr><tr><td style='text-align: center;'>远程复制</td><td style='text-align: center;'>在两个 Oracle ZFS Storage Appliance 产品之间复制。1:N、N:1、手动、定时、持续（包含在机柜式系统配置中）</td></tr><tr><td style='text-align: center;'>加密</td><td style='text-align: center;'>可在项目/共享/LUN 级别或池级别采用强加密算法（AES 256/192/128）进行双层加密。您可在本地密钥存储库中管理加密密钥，也可使用 Oracle 密钥管理器进行集中管理。机柜式系统配置中包含数据加密特性。</td></tr></table>

## Oracle 支持服务

Oracle 标准支持服务提供全面的系统支持，可帮助您主动管理 Oracle 存储系统。当发生问题时，Oracle 能快速地为用户提供解决方案和硬件服务，确保业务信息 24/7 的可用性。

Oracle 白金服务为相应配置的 Oracle ZFS 机柜式存储系统提供更高级别的服务。当使用 Oracle ZFS ZS11-2 机柜式存储系统作为 Oracle 集成系统的备份解决方案时，用户可获得 Oracle 白金服务支持。如需了解 Oracle 白金服务的最低配置要求，请咨询您的客户代表。

在 Oracle 高级客户支持服务下，您可以藉由一支专门支持团队来获取关键任务支持，在主动指导的帮助下量身定制存储系统、优化性能、加强竞争优势；还可以通过预防性监视服务，实现高可用性和优化的系统性能。

有关 Oracle 标准支持服务、Oracle 白金服务和 Oracle 高级客户支持服务的更多信息，请联系 Oracle 代表或 Oracle 授权合作伙伴，或访问 oracle.com/cn/support 或 oracle.com/cn/customer-success/run-and-operate/。

## 联系我们

请致电 400-699-8888 或访问 oracle.com/cn。中国地区的用户请访问 oracle.com/cn/corporate/contact/，查找您当地 Oracle 办事处的电话号码。

blogs.oracle.com



<div style="text-align: center;"><img src="imgs/img_in_image_box_106_1301_132_1326.jpg" alt="Image" width="2%" /></div>


<div style="text-align: center;"><img src="imgs/img_in_image_box_323_1302_349_1326.jpg" alt="Image" width="2%" /></div>


facebook.com/oracle

<div style="text-align: center;"><img src="imgs/img_in_image_box_574_1302_598_1325.jpg" alt="Image" width="1%" /></div>


twitter.com/oracle

版权所有 $ ^{©} $ 2025，Oracle和/或其关联公司。本文档仅供参考，此处内容若有更改，恕不另行通知。本文档不保证没有错误，也不受其他任何口头表达或法律暗示的担保或条件的约束，包括对特定用途的适销性或适用性的暗示担保和条件。我们特别声明拒绝承担与本文档有关的任何责任，本文档不直接或间接形成任何契约义务。未经预先书面许可，不允许以任何形式或任何方式（电子或机械的）、出于任何目的复制或传播本文档。

Oracle、Java、MySQL 和 NetSuite 是 Oracle 和/或其关联公司的注册商标。其它名称可能是其各自所有者的商标。