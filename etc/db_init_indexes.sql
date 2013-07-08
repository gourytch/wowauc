BEGIN; 

CREATE INDEX idx_auc_lots_item_id ON auc.lots (item_id);
CREATE INDEX idx_auc_lots_owner ON auc.lots (owner);
CREATE INDEX idx_auc_lots_t_open ON auc.lots (t_open);
CREATE INDEX idx_auc_lots_t_close ON auc.lots (t_close);

COMMIT;

