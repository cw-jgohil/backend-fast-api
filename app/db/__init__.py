from app.db.session import SessionLocal

def seed_rbac():
    # Import models inside function to avoid circular imports
    from app.models.user import Role, Module, Resource, Permission, RoleResourcePermission
    
    db = SessionLocal()
    # Define roles
    roles = [
        Role(name="Christie Admin", description="All data points, access, and logs"),
        Role(name="Client Admin", description="All client data points, parameters, and history"),
        Role(name="Client Technician", description="All client data points, parameters, and history"),
        Role(name="Client Cleaner", description="View and log cleans only"),
        Role(name="Service Technician", description="View only"),
    ]
    # Define modules
    modules = [
        Module(name="Cleaning", description="Cleaning interface and logs"),
        Module(name="Firmware", description="Firmware update and versioning"),
        Module(name="Configuration", description="Device configuration and parameters"),
        Module(name="Telemetry", description="Device telemetry and data points"),
        Module(name="OTA Update", description="Over-the-air firmware updates"),
        Module(name="Device Management", description="Device registration and management"),
        Module(name="LTE", description="LTE module and telemetry"),
    ]
    # Define resources
    resources = [
        Resource(name="cleaning_screen", description="Cleaning screen", module=modules[0]),
        Resource(name="firmware_update", description="Firmware update screen", module=modules[1]),
        Resource(name="config_params", description="Configuration parameters", module=modules[2]),
        Resource(name="telemetry_data", description="Telemetry data", module=modules[3]),
        Resource(name="ota_update", description="OTA update", module=modules[4]),
        Resource(name="device_registration", description="Device registration", module=modules[5]),
        Resource(name="lte_telemetry", description="LTE telemetry", module=modules[6]),
    ]
    # Define permissions
    permissions = [
        Permission(name="view", description="View resource"),
        Permission(name="edit", description="Edit resource"),
        Permission(name="register", description="Register clean or device"),
        Permission(name="update", description="Update resource"),
        Permission(name="delete", description="Delete resource"),
        Permission(name="upload_firmware", description="Upload firmware"),
        Permission(name="read_param", description="Read parameter"),
        Permission(name="write_param", description="Write parameter"),
    ]
    db.add_all(roles + modules + resources + permissions)
    db.commit()
    # Assign permissions to roles (example, can be extended)
    # Cleaner: view and register on cleaning_screen
    cleaner_role = db.query(Role).filter_by(name="Client Cleaner").first()
    cleaning_resource = db.query(Resource).filter_by(name="cleaning_screen").first()
    view_perm = db.query(Permission).filter_by(name="view").first()
    register_perm = db.query(Permission).filter_by(name="register").first()
    db.add_all([
        RoleResourcePermission(role_id=cleaner_role.id, resource_id=cleaning_resource.id, permission_id=view_perm.id),
        RoleResourcePermission(role_id=cleaner_role.id, resource_id=cleaning_resource.id, permission_id=register_perm.id),
    ])
    # Service Technician: view only on telemetry_data
    tech_role = db.query(Role).filter_by(name="Service Technician").first()
    telemetry_resource = db.query(Resource).filter_by(name="telemetry_data").first()
    db.add(RoleResourcePermission(role_id=tech_role.id, resource_id=telemetry_resource.id, permission_id=view_perm.id))
    # Christie Admin: all permissions on all resources
    admin_role = db.query(Role).filter_by(name="Christie Admin").first()
    for resource in db.query(Resource).all():
        for perm in db.query(Permission).all():
            db.add(RoleResourcePermission(role_id=admin_role.id, resource_id=resource.id, permission_id=perm.id))
    db.commit()
    db.close()

if __name__ == "__main__":
    seed_rbac()
