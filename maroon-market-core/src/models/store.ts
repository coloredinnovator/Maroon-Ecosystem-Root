import { Store as MedusaStore } from "@medusajs/medusa";
import { Entity, Column } from "typeorm";

@Entity()
export class Store extends MedusaStore {
  // Extending the core Medusa Store entity for the Maroon Ecosystem
  
  @Column({ type: "boolean", default: false })
  is_verified_black_owned: boolean;

  @Column({ type: "varchar", nullable: true })
  governance_hash: string;

  @Column({ type: "boolean", default: false })
  accepts_maroon_currency: boolean;

  @Column({ type: "boolean", default: false })
  ebt_eligible: boolean;
  
  @Column({ type: "varchar", nullable: true })
  co_op_id: string;
}
