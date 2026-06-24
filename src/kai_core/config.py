from pydantic import BaseModel, ConfigDict
from pydantic_settings import BaseSettings
from ipaddress import IPv4Address

from src.kai_core.utils.custom_types import LogLevel, NetworkProtocol

class SystemConfig(BaseModel):
    log_level: LogLevel = LogLevel.DEBUG

class NetworkConfig(BaseModel):
    node_id: str = "alien-wsl"
    protocol: NetworkProtocol = NetworkProtocol.TCP
    host_incoming: IPv4Address = IPv4Address("127.0.0.1")
    host_target: IPv4Address = IPv4Address("100.89.160.118")
    port_incoming: int = 5555
    port_target: int = 5556

class GlobalConfig(BaseSettings):
    model_config = ConfigDict(frozen=True)
    system: SystemConfig = SystemConfig()
    network: NetworkConfig = NetworkConfig()

settings = GlobalConfig()
