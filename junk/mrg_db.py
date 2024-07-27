# from sqlalchemy import create_engine, Column, Integer, String, Boolean, ForeignKey, DateTime, Text, SmallInteger, BigInteger, insert
# from sqlalchemy.orm import Session, relationship, sessionmaker, declarative_base
# from sqlalchemy.inspection import inspect
# import datetime
# import logging



# Base = declarative_base()

# # Define the SQLite engine
# DATABASE_URL = "sqlite:///./db/mrg2.db"
# engine = create_engine(DATABASE_URL, echo=True)

# # Define the session
# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
# session = SessionLocal()
# logging.getLogger('sqlalchemy').setLevel(logging.ERROR)
# class BaseModel(Base):
#     __abstract__ = True
#     uuid = Column(String, primary_key=True)
#     create_date = Column(DateTime, default=datetime.datetime.utcnow)
#     update_date = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

# # NamedObject equivalent
# class NamedObject(BaseModel):
#     __abstract__ = True
#     name = Column(String)
#     description = Column(Text, nullable=True)
#     tags = Column(Text, nullable=True)

# # PackageRepositories
# class PackageRepositories(NamedObject):
#     __tablename__ = 'package_repositories'
#     url = Column(String)
#     system = Column(Boolean, default=False)
#     packages = relationship('Packages', back_populates='package_repository')
    

# # Packages
# class Packages(NamedObject):
#     __tablename__ = 'packages'
#     version = Column(String, nullable=True)
#     repository = Column(String, nullable=True)
#     branch = Column(String, nullable=True)
#     commit = Column(String, nullable=True)
#     parameters = Column(Text, nullable=True)
#     settings = Column(Text, nullable=True)
#     package_repository_uuid = Column(String, ForeignKey('package_repositories.uuid'), nullable=True)
#     package_repository = relationship('PackageRepositories', back_populates='packages')
#     workflows = relationship('Workflows', back_populates='package')
#     jobs = relationship('Jobs', back_populates='package')
#     apis = relationship('Api', back_populates='package')

# # Categories
# class Categories(NamedObject):
#     __tablename__ = 'categories'
#     uuid = Column(String, primary_key=True)
#     icon = Column(String)
#     system = Column(Boolean, default=False)
#     order = Column(Integer, default=1)
#     parent_uuid = Column(String, ForeignKey('categories.uuid'), nullable=True)
#     parent = relationship('Categories', remote_side=[uuid], back_populates='children')
#     children = relationship('Categories', back_populates='parent')
#     workflows = relationship('Workflows', back_populates='category')

# # Workflows
# class Workflows(NamedObject):
#     __tablename__ = 'workflows'
#     rating = Column(SmallInteger, default=0)
#     order = Column(Integer, default=1)
#     favourite = Column(Boolean, default=False)
#     hidden = Column(Boolean, default=False)
#     system = Column(Boolean, default=False)
#     times_used = Column(Integer, default=0)
#     contents = Column(Text, nullable=True)
#     nodes_values = Column(Text, nullable=True)
#     settings = Column(Text, nullable=True)
#     run_values = Column(Text, nullable=True)
#     package_uuid = Column(String, ForeignKey('packages.uuid'), nullable=True)
#     category_uuid = Column(String, ForeignKey('categories.uuid'), nullable=True)
#     package = relationship('Packages', back_populates='workflows')
#     category = relationship('Categories', back_populates='workflows')
#     batch_requests = relationship('BatchRequests', back_populates='workflow')
    

# # BatchRequests
# class BatchRequests(BaseModel):
#     __tablename__ = 'batch_requests'
#     workflow_uuid = Column(String, ForeignKey('workflows.uuid'), nullable=True)
#     api_uuid = Column(String, ForeignKey('api.uuid'), nullable=True)
#     job_uuid = Column(String, ForeignKey('jobs.uuid'), nullable=True)
#     secondary_uuid = Column(String, nullable=True)
#     client_id = Column(String, nullable=True)
#     run_settings = Column(Text)
#     total = Column(Integer)
#     contents = Column(Text, nullable=True)
#     run_type = Column(String)
#     current = Column(Integer)
#     order = Column(BigInteger)
#     status = Column(String, nullable=True)
#     start_date = Column(DateTime, nullable=True)
#     end_date = Column(DateTime, nullable=True)
#     nodes_values = Column(Text, nullable=True)
#     run_values = Column(Text, nullable=True)
#     current_values = Column(Text, nullable=True)
#     workflow = relationship('Workflows', back_populates='batch_requests')
#     api = relationship('Api', back_populates='batch_requests')
#     job = relationship('Jobs', back_populates='batch_requests')
#     queue_steps = relationship('QueueSteps', back_populates='queued_run')

# # QueueSteps
# class QueueSteps(BaseModel):
#     __tablename__ = 'queue_steps'
#     queued_run_uuid = Column(String, ForeignKey('batch_requests.uuid'), nullable=True)
#     run_value = Column(Text)
#     status = Column(String)
#     step = Column(Integer)
#     server = Column(Integer)
#     retry = Column(Integer, default=0)
#     error = Column(Text, nullable=True)
#     create_date = Column(DateTime, default=datetime.datetime.utcnow)
#     start_date = Column(DateTime, nullable=True)
#     update_date = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
#     end_date = Column(DateTime, nullable=True)
#     batch_request = relationship('BatchRequests', back_populates='queue_steps')
#     outputs = relationship('Outputs', back_populates='queue_step')
    

# # Outputs
# class Outputs(BaseModel):
#     __tablename__ = 'outputs'
#     queue_step_uuid = Column(String, ForeignKey('queue_steps.uuid'), nullable=True)
#     value = Column(Text)
#     order = Column(Integer)
#     node_id = Column(Integer)
#     output_type = Column(String)
#     create_date = Column(DateTime, default=datetime.datetime.utcnow)
#     update_date = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
#     rating = Column(SmallInteger, default=0)
#     queue_step = relationship('QueueSteps', back_populates='outputs')
#     output_links = relationship('OutputLinks', back_populates='output')
    

# # OutputLinks
# class OutputLinks(BaseModel):
#     __tablename__ = 'output_links'
#     output_uuid = Column(String, ForeignKey('outputs.uuid'), nullable=True)
#     selection_item_uuid = Column(String, ForeignKey('selection_items.uuid'), nullable=True)
#     output = relationship('Outputs', back_populates='output_links')
#     selection_item = relationship('SelectionItems', back_populates='output_links')
    

# # Settings
# class Settings(NamedObject):
#     __tablename__ = 'settings'
#     setting_type = Column(String)
#     value = Column(Text, nullable=True)
#     value_type = Column(String, nullable=True)
#     value_type_options = Column(Text, nullable=True)

# class NamedPackageObject(NamedObject): #js model
#     __abstract__ = True    
#     package_uuid = Column(String, ForeignKey('packages.uuid'), nullable=True)
#     category_uuid = Column(String, ForeignKey('categories.uuid'), nullable=True)
    

# class WorkflowExtenders(NamedPackageObject): #js model
#     __abstract__ = True    
#     workflows = Column(Text, nullable=True)
#     enabled = Column(Boolean, default=True)
#     runs = Column(Integer, default=0)
    
# class Jobs(WorkflowExtenders): #js model
#     __tablename__ = 'jobs'    
#     cron = Column(String, nullable=False)
#     package = relationship('Packages', back_populates='jobs')
#     batch_requests = relationship('BatchRequests', back_populates='job')
    

# class Api(WorkflowExtenders): #js model
#     __tablename__ = 'api'
#     endpoint = Column(String, nullable=False)
#     parameters = Column(Text, nullable=True)
#     package = relationship('Packages', back_populates='apis')
#     batch_requests = relationship('BatchRequests', back_populates='api')


# class SelectionItems(NamedObject):
#     __tablename__ = 'selection_items'
#     alias = Column(String)
#     comfy_name = Column(String, nullable=True)
#     comments = Column(Text, nullable=True)
#     times_used = Column(Integer, default=0)
#     rating = Column(SmallInteger, default=0)
#     text = Column(Text)
#     hidden = Column(Boolean, default=False)
#     favorite = Column(Boolean, default=False)
#     field = Column(String)
#     field_type = Column(String)
#     node_type = Column(String)
#     path = Column(String, nullable=True)
#     image = Column(String, nullable=True)
#     thumbnail = Column(String, nullable=True)
#     output_links = relationship('OutputLinks', back_populates='selection_item')


# # Create all tables
# Base.metadata.create_all(bind=engine)

# def create_default_data():
#     #session.add(PackageRepositories(uuid="f42cd12c-4c7a-451b-a1f4-ad2d2a6fe28f", name="Mr.G official packages", url="https://github.com/RazvanManolache/Mr.G-AI-Packages-List", system=True))   
#     stmt = insert(PackageRepositories).values({"uuid":"f42cd12c-4c7a-451b-a1f4-ad2d2a6fe28f", "name":"Mr.G official packages", "url":"https://github.com/RazvanManolache/Mr.G-AI-Packages-List", "system":True})
    
#     stmt = stmt.prefix_with("OR REPLACE")
#     session.execute(stmt)
#     session.commit()
    
    
#     #session.add(Categories(uuid="00000000-0001-0000-0000-000000000000", name="Favourites", icon="x-fa fa-star", system=True, order=-9999))
#     stmt = insert(Categories).values({"uuid":"00000000-0001-0000-0000-000000000000", "name":"Favourites", "icon":"x-fa fa-star", "system":True, "order":-9999})
#     stmt = stmt.prefix_with("OR REPLACE")
#     session.execute(stmt)
#     session.commit()
    

#     #session.add(Categories(uuid="00000000-0003-0000-0000-000000000000", name="No category", icon="x-fa fa-question", system=True, order=-9997))
#     stmt = insert(Categories).values({"uuid":"00000000-0003-0000-0000-000000000000", "name":"No category", "icon":"x-fa fa-question", "system":True, "order":-9997})
#     stmt = stmt.prefix_with("OR REPLACE")
#     session.execute(stmt)
#     session.commit()
    
#     #session.add(Categories(uuid="00000000-0002-0000-0000-000000000000", name="All", icon="x-fa fa-globe", system=True, order=-9998))
#     stmt = insert(Categories).values({"uuid":"00000000-0002-0000-0000-000000000000", "name":"All", "icon":"x-fa fa-globe", "system":True, "order":-9998})
#     stmt = stmt.prefix_with("OR REPLACE")
#     session.execute(stmt)
#     session.commit()
    
    

# create_default_data()

# def get_queue_step_by_id(step_id):
#     return session.query(QueueSteps).get(step_id)

# def get_apis():
#     return session.query(Api)

# def insert_batch_request(data):
#     return session.add(BatchRequests(**data))

# def update_queue_step(data):
#     return session.merge(data)

# def get_batch_request_status_for_uuid_list(uuids):
#     return session.query(BatchRequests).filter(BatchRequests.uuid.in_(uuids)).all()

# def get_all_outputs_for_run(uuid):
#     return session.query(Outputs).join(QueueSteps).join(BatchRequests).filter(BatchRequests.uuid==uuid).all()

# def get_workflow(uuid):
#     return session.query(Workflows).get(uuid)

# def update_job_runs(uuid, runs):
#     job = session.query(Jobs).get(uuid)
#     job.runs = runs
#     session.commit()
    
# def update_api_runs(uuid, runs):
#     api = session.query(Api).get(uuid)
#     api.runs = runs
#     session.commit()
    
# def get_all_queue_steps_by_statuses_other_than(statuses):
#     return session.query(QueueSteps).filter(QueueSteps.status.notin_(statuses)).all()

# def insert_output(data):
#     return session.add(Outputs(**data))

# def get_queue_steps_by_statuses_other_than(queued_run_uuid, statuses):
#     return session.query(QueueSteps).filter(QueueSteps.queued_run_uuid==queued_run_uuid, QueueSteps.status.notin_(statuses)).all()

# def update_batch_request(data):
#     return session.merge(data)

# def get_queued_run_by_id(uuid):
#     return session.query(BatchRequests).get(uuid)

# def get_batch_requests_by_statuses(statuses):
#     return session.query(BatchRequests).filter(BatchRequests.status.in_(statuses)).all()

# def insert_queue_step(data):
#     return session.add(QueueSteps(**data))
 
# def get_batch_requests_max_order():
#     rec = session.query(BatchRequests).order_by(BatchRequests.order.desc()).first()
#     if rec:
#         return rec.order
#     return 0

# def model_to_dict(obj):
#     return {c.key: getattr(obj, c.key) for c in inspect(obj).mapper.column_attrs}

# def get_categories():
#     return session.query(Categories)

# def get_selection_items(field, node_type):
#     return session.query(SelectionItems).filter(SelectionItems.field==field, SelectionItems.node_type==node_type)

# def get_selection_item(uuid):
#     return session.query(SelectionItems).get(uuid)

# def upsert_selection_items(data):
#     if "uuid" in data:
#         item = session.query(SelectionItems).get(data["uuid"])
#         for key, value in data.items():
#             setattr(item, key, value)
#     else:
#         item = SelectionItems(**data)
#         session.add(item)
#     session.commit()
#     return model_to_dict(item)

# def delete_selection_items(uuid):
#     item = session.query(SelectionItems).get(uuid)
#     session.delete(item)
#     session.commit()