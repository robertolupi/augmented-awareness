import { Notice } from "obsidian";

export class ProgressNotice {
	private notice: Notice;
	private barEl: HTMLProgressElement;
	private statusEl: HTMLElement;
	private cancelBtn: HTMLButtonElement;

	constructor(title: string, total: number, onCancel: () => void) {
		const docFrag = document.createDocumentFragment();
		const container = docFrag.createDiv({ cls: "aww-retro-progress" });

		const titleEl = container.createDiv({
			cls: "aww-retro-progress-title",
		});
		titleEl.setText(title);

		this.barEl = container.createEl("progress", {
			cls: "aww-retro-progress-bar",
		});
		this.barEl.max = Math.max(1, total);
		this.barEl.value = 0;
		this.barEl.style.width = "100%";
		this.barEl.style.margin = "6px 0";

		const row = container.createDiv({
			cls: "aww-retro-progress-row",
		});
		row.style.display = "flex";
		row.style.justifyContent = "space-between";
		row.style.alignItems = "center";

		this.statusEl = row.createDiv({
			cls: "aww-retro-progress-status",
		});
		this.statusEl.setText(`0 / ${total}`);

		this.cancelBtn = row.createEl("button", {
			text: "Cancel",
			cls: "mod-warning aww-retro-progress-cancel",
		});
		this.cancelBtn.style.marginLeft = "12px";
		this.cancelBtn.addEventListener("click", () => {
			this.cancelBtn.disabled = true;
			this.cancelBtn.setText("Cancelling...");
			onCancel();
		});

		// Duration 0 creates a persistent Notice until .hide() is called
		this.notice = new Notice(docFrag, 0);
	}

	update(completed: number, total: number, message: string): void {
		this.barEl.max = Math.max(1, total);
		this.barEl.value = completed;
		this.statusEl.setText(`[${completed}/${total}] ${message}`);
	}

	complete(message: string): void {
		this.notice.hide();
		new Notice(message, 5000);
	}

	cancel(message = "Retrospective generation cancelled."): void {
		this.notice.hide();
		new Notice(message, 4000);
	}

	error(message: string): void {
		this.notice.hide();
		new Notice(`Generation failed: ${message}`, 7000);
	}
}
