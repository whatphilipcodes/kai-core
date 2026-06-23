from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings
from ipaddress import IPv4Address

from src.kai_core.utils.custom_types import LogLevel, NetworkProtocol

class SystemConfig(BaseModel):
    log_level: LogLevel = LogLevel.DEBUG

class NetworkConfig(BaseModel):
    protocol: NetworkProtocol = NetworkProtocol.TCP
    host_in: IPv4Address = IPv4Address("100.110.102.87") # ctech workstation -> speaker
    host_out: IPv4Address = IPv4Address("100.89.160.118") # alienware laptop -> llm
    port_in: int = 5554
    port_out: int = 5555

class GlobalConfig(BaseSettings):
    model_config = ConfigDict(frozen=True)
    system: SystemConfig = SystemConfig()
    network: NetworkConfig = NetworkConfig()

settings = GlobalConfig()
